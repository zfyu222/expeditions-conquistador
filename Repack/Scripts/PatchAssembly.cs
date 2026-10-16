using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using System.Text.Json;
using System.Security.Cryptography;
using dnlib.DotNet;
using dnlib.DotNet.Emit;
using dnlib.DotNet.Writer;

class PatchAssembly
{
    class Record
    {
        public string method_token { get; set; }
        public string class_name { get; set; }
        public string text { get; set; }
        public string translation { get; set; }
    }
    static void Require(bool condition, string message) { if (!condition) throw new Exception(message); }
    static MethodDef Method(ModuleDef module, string type, string name, int parameters)
    { return module.Types.Single(t => t.Name == type).Methods.Single(m => m.Name == name && m.MethodSig.Params.Count == parameters); }
    static void Main(string[] args)
    {
        string original = args[0], helperPath = args[1], mapPath = args[2], output = args[3];
        string sourceHash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(original))).ToLowerInvariant();
        Require(sourceHash == "1b1dbf3001f5c1fc3909c694e59fc3aa57f39446948e8055319c5cfac02cf8a8", "Unsupported original assembly");
        var module = ModuleDefMD.Load(original);
        var helper = ModuleDefMD.Load(helperPath);
        var helperType = helper.Types.Single(t => t.FullName == "Zfy.Localization.ChineseLayout");
        var importer = new Importer(module);
        var build = importer.Import(helperType.Methods.Single(m => m.Name == "BuildChunks"));
        var measure = importer.Import(helperType.Methods.Single(m => m.Name == "Measure"));
        var display = importer.Import(helperType.Methods.Single(m => m.Name == "UseDisplayText"));
        Require(!helper.GetAssemblyRefs().Any(a => a.Name == "Assembly-CSharp"), "Helper must not reference game-internal types");
        var savedType = helper.Types.Single(t => t.FullName == "Zfy.Localization.SavedDisplay");
        var savedBio = importer.Import(savedType.Methods.Single(m => m.Name == "SavedBio"));
        var savedTitle = importer.Import(savedType.Methods.Single(m => m.Name == "SavedTitle"));
        var savedDescription = importer.Import(savedType.Methods.Single(m => m.Name == "SavedDescription"));
        var wraps = helperType.Methods.Where(m => m.Name == "Wrap").ToDictionary(m => m.MethodSig.Params.Count, m => importer.Import(m));
        var entries = JsonSerializer.Deserialize<List<Record>>(File.ReadAllText(mapPath));
        var grouped = entries.GroupBy(r => r.method_token + "|" + r.text);
        int translated = 0, direct = 0, deferred = 0, translatedResult = 0;
        foreach (var group in grouped)
        {
            var first = group.First();
            uint token = Convert.ToUInt32(first.method_token.Substring(2), 16);
            var method = module.ResolveToken(token) as MethodDef;
            Require(method != null && method.DeclaringType.Name == first.class_name, "Method identity mismatch");
            var translations = group.Select(r => r.translation).Distinct().ToArray();
            Require(translations.Length == 1, "Ambiguous repeated display literal");
            var instructions = method.Body.Instructions.Where(i => i.OpCode == OpCodes.Ldstr && (string)i.Operand == first.text).ToArray();
            if (first.method_token == "0x06001100" || first.method_token == "0x06001042")
            {
                Require(instructions.Length == group.Count(), "Lookup occurrence mismatch");
                foreach (var instruction in instructions)
                {
                    int index = method.Body.Instructions.IndexOf(instruction);
                    var call = method.Body.Instructions.Skip(index+1).First(i => i.Operand is IMethod);
                    Require(((IMethod)call.Operand).Name == "ShowTranslation", "Unexpected lookup target");
                    int after = method.Body.Instructions.IndexOf(call)+1;
                    method.Body.Instructions.Insert(after, Instruction.Create(OpCodes.Ldstr, translations[0]));
                    method.Body.Instructions.Insert(after+1, Instruction.Create(OpCodes.Call, display));
                }
                translated += instructions.Length; translatedResult += instructions.Length;
                continue;
            }
            if (first.class_name != "VersionLabel")
                instructions = instructions.Where(i => {
                    int next = method.Body.Instructions.IndexOf(i)+1;
                    var constructor = next < method.Body.Instructions.Count ? method.Body.Instructions[next] : null;
                    return constructor != null && constructor.OpCode == OpCodes.Newobj && ((IMethod)constructor.Operand).DeclaringType.FullName == "UnityEngine.GUIContent";
                }).ToArray();
            Require(instructions.Length == group.Count(), "Literal occurrence mismatch: " + method.FullName + ": " + first.text + " expected=" + group.Count() + " actual=" + instructions.Length);
            // These GUIContent.text values also drive difficulty/options keys and saves.
            // Keep them original and translate a temporary content copy only when drawn.
            if (first.class_name == "OptionsMenu" || first.class_name == "CampaignSelectionGUI" || first.class_name == "HostGUI")
                deferred += instructions.Length;
            else
            {
                foreach (var instruction in instructions) instruction.Operand = translations[0];
                direct += instructions.Length;
            }
            translated += instructions.Length;
        }
        Require(translated == 34, "Managed translation count mismatch");
        int displayCalls = 0;
        foreach (var type in module.Types.Where(t => new[]{"ComboBox","OptionsMenu","CampaignSelectionGUI","HostGUI"}.Contains(t.Name.String)))
        foreach (var method in type.Methods.Where(m => m.HasBody))
        foreach (var instruction in method.Body.Instructions)
        {
            var called = instruction.Operand as IMethod;
            if (called == null || called.DeclaringType.FullName != "UnityEngine.GUI" || (called.Name != "Button" && called.Name != "Label")) continue;
            var replacement = helperType.Methods.FirstOrDefault(m => m.Name == called.Name && m.MethodSig.Params.Count == called.MethodSig.Params.Count
                && m.MethodSig.Params.Select(p=>p.FullName).SequenceEqual(called.MethodSig.Params.Select(p=>p.FullName)));
            if (replacement != null) { instruction.Operand = importer.Import(replacement); displayCalls++; }
        }
        Require(direct == 5 && deferred == 16 && translatedResult == 13 && displayCalls > 10, "Display routing count mismatch");
        int savedBioCalls = 0, savedTitleCalls = 0, savedDescriptionCalls = 0;
        foreach (var type in module.Types.Where(t => t.Name.String.EndsWith("GUI")))
        foreach (var method in type.Methods.Where(m => m.HasBody))
        foreach (var instruction in method.Body.Instructions.ToArray())
        {
            IMethod replacement = null;
            var field = instruction.Operand as IField;
            var called = instruction.Operand as IMethod;
            if (instruction.OpCode == OpCodes.Ldfld && field != null && field.DeclaringType.Name == "Follower" && field.Name == "followerBio")
            { replacement = savedBio; savedBioCalls++; }
            if (type.Name == "InfoGUI" && called != null && called.DeclaringType.Name == "Goal")
            {
                if (called.Name == "get_GoalTitle") { replacement = savedTitle; savedTitleCalls++; }
                if (called.Name == "get_GoalText") { replacement = savedDescription; savedDescriptionCalls++; }
            }
            if (replacement != null)
                method.Body.Instructions.Insert(method.Body.Instructions.IndexOf(instruction)+1, Instruction.Create(OpCodes.Call,replacement));
        }
        Require(savedBioCalls >= 2 && savedTitleCalls == 1 && savedDescriptionCalls == 1, "Saved display routing mismatch");
        int tutorialPages=0, tutorialHeaders=0;
        var styleLibrary=module.Types.Single(t=>t.Name=="GUIStyleLibrary");
        var styleInstance=styleLibrary.Methods.Single(m=>m.Name=="get_Instance");
        var tutorialStyle=styleLibrary.Fields.Single(f=>f.Name=="headline16Style");
        foreach(var type in module.Types.Where(t=>t.Name=="TutorialMiddleDrawer" || t.Name=="TutorialController"))
        foreach(var method in type.Methods.Where(m=>m.HasBody))
        foreach(var instruction in method.Body.Instructions.ToArray())
        {
            var called=instruction.Operand as IMethod;
            if(called==null || called.DeclaringType.FullName!="UnityEngine.GUI" || called.Name!="DrawTexture" || called.MethodSig.Params.Count!=2) continue;
            int offset=method.Body.Instructions.IndexOf(instruction);
            var field=offset>0?method.Body.Instructions[offset-1].Operand as IField:null;
            string replacement=null;
            if(type.Name=="TutorialMiddleDrawer" && field!=null && field.Name=="image") { replacement="DrawTutorialPage"; tutorialPages++; }
            if(type.Name=="TutorialController" && field!=null && field.Name=="tutorialHeadlineEN") { replacement="DrawTutorialHeader"; tutorialHeaders++; }
            if(replacement==null) continue;
            method.Body.Instructions.Insert(offset,Instruction.Create(OpCodes.Call,styleInstance));
            method.Body.Instructions.Insert(offset+1,Instruction.Create(OpCodes.Ldfld,tutorialStyle));
            instruction.OpCode=OpCodes.Call;
            instruction.Operand=importer.Import(helperType.Methods.Single(m=>m.Name==replacement));
            method.Body.MaxStack++;
        }
        Require(tutorialPages==1 && tutorialHeaders==1,"Tutorial drawing scope mismatch");
        var dialog = module.Types.Single(t => t.Name == "DialogGUI");
        var prepare = dialog.Methods.Single(m => m.Name == "PrepareStringForDisplay");
        prepare.Body = new CilBody {MaxStack = 8};
        var il = prepare.Body.Instructions;
        var neutralChunk = helper.Types.Single(t => t.FullName == "Zfy.Localization.ChineseChunk");
        var chunkArray = new Local(new SZArraySig(importer.Import(neutralChunk).ToTypeSig()));
        var result = new Local(prepare.MethodSig.RetType);
        var chunkIndex = new Local(module.CorLibTypes.Int32);
        prepare.Body.Variables.Add(chunkArray); prepare.Body.Variables.Add(result); prepare.Body.Variables.Add(chunkIndex);
        prepare.Body.InitLocals = true;
        var listType = prepare.MethodSig.RetType.ToTypeDefOrRef();
        var listCtor = new MemberRefUser(module, ".ctor", MethodSig.CreateInstance(module.CorLibTypes.Void), listType);
        var listAdd = new MemberRefUser(module, "Add", MethodSig.CreateInstance(module.CorLibTypes.Void, new GenericVar(0)), listType);
        var chunkCtor = module.Types.Single(t => t.Name == "WordChunk").Methods.Single(m => m.IsInstanceConstructor);
        var convert = Instruction.Create(OpCodes.Stloc, chunkArray);
        var choice = Instruction.Create(OpCodes.Nop);
        var description = Instruction.Create(OpCodes.Nop);
        var speech = Instruction.Create(OpCodes.Nop);
        il.Add(Instruction.Create(OpCodes.Ldarg_2)); il.Add(Instruction.CreateLdcI4(3)); il.Add(Instruction.Create(OpCodes.Beq, choice));
        il.Add(Instruction.Create(OpCodes.Ldarg_2)); il.Add(Instruction.CreateLdcI4(0)); il.Add(Instruction.Create(OpCodes.Beq, description));
        il.Add(Instruction.Create(OpCodes.Ldarg_2)); il.Add(Instruction.CreateLdcI4(1)); il.Add(Instruction.Create(OpCodes.Beq, speech));
        Action<Instruction,string,string> block = (label,prefix,color) =>
        {
            if (label != null) il.Add(label);
            il.Add(Instruction.Create(OpCodes.Ldarg_1));
            foreach (string name in new [] {prefix,prefix+"italics",prefix+"bold",color})
            { il.Add(Instruction.Create(OpCodes.Ldarg_0)); il.Add(Instruction.Create(OpCodes.Ldfld, dialog.Fields.Single(f => f.Name == name))); }
            il.Add(Instruction.Create(OpCodes.Call, build)); il.Add(Instruction.Create(OpCodes.Br, convert));
        };
        block(null,"playerdialogstyle","playerdialogstylebold");
        block(choice,"choicestyle","choicestylecolor");
        block(description,"descripstyle","descripstylebold");
        block(speech,"dialogstyle","dialogstylebold");
        il.Add(convert);
        il.Add(Instruction.Create(OpCodes.Newobj, listCtor)); il.Add(Instruction.Create(OpCodes.Stloc, result));
        il.Add(Instruction.CreateLdcI4(0)); il.Add(Instruction.Create(OpCodes.Stloc, chunkIndex));
        var test = Instruction.Create(OpCodes.Ldloc, chunkIndex);
        var loop = Instruction.Create(OpCodes.Ldloc, result);
        il.Add(Instruction.Create(OpCodes.Br, test)); il.Add(loop);
        foreach (string field in new[]{"guistyle", "text"})
        {
            il.Add(Instruction.Create(OpCodes.Ldloc, chunkArray)); il.Add(Instruction.Create(OpCodes.Ldloc, chunkIndex));
            il.Add(Instruction.Create(OpCodes.Ldelem_Ref));
            il.Add(Instruction.Create(OpCodes.Ldfld, importer.Import(neutralChunk.Fields.Single(f => f.Name == field))));
        }
        il.Add(Instruction.Create(OpCodes.Newobj, chunkCtor)); il.Add(Instruction.Create(OpCodes.Callvirt, listAdd));
        il.Add(Instruction.Create(OpCodes.Ldloc, chunkIndex)); il.Add(Instruction.CreateLdcI4(1)); il.Add(Instruction.Create(OpCodes.Add));
        il.Add(Instruction.Create(OpCodes.Stloc, chunkIndex));
        il.Add(test); il.Add(Instruction.Create(OpCodes.Ldloc, chunkArray)); il.Add(Instruction.Create(OpCodes.Ldlen)); il.Add(Instruction.Create(OpCodes.Conv_I4));
        il.Add(Instruction.Create(OpCodes.Blt, loop)); il.Add(Instruction.Create(OpCodes.Ldloc, result)); il.Add(Instruction.Create(OpCodes.Ret));
        var space = dialog.Methods.Single(m => m.Name == "GetWhiteSpaceWidth");
        space.Body = new CilBody {MaxStack = 1}; space.Body.Instructions.Add(Instruction.CreateLdcI4(0)); space.Body.Instructions.Add(Instruction.Create(OpCodes.Ret));
        int wrapCount = 0, measureCount = 0;
        foreach (var type in module.Types.Where(t => t.Name == "DialogGUI" || t.Name == "DisplayComponent"))
        foreach (var method in type.Methods.Where(m => m.HasBody))
        {
            if (method.Name == "ParseText" || method.Name == "ParseTextPages")
            {
                int count = method.MethodSig.Params.Count;
                Require(count >= 4 && count <= 6, "Unexpected wrapping signature");
                method.Body = new CilBody {MaxStack = 8};
                var ops = method.Body.Instructions;
                for (int i=1;i<=4;i++) ops.Add(Instruction.Create(OpCodes.Ldarg, method.Parameters[i]));
                if (count == 4)
                {
                    var height = new Local(module.CorLibTypes.Int32); method.Body.Variables.Add(height); method.Body.InitLocals = true;
                    ops.Add(Instruction.Create(OpCodes.Ldloca, height));
                }
                else for (int i=5;i<=count;i++) ops.Add(Instruction.Create(OpCodes.Ldarg, method.Parameters[i]));
                ops.Add(Instruction.Create(OpCodes.Call, wraps[count == 6 ? 6 : 5])); ops.Add(Instruction.Create(OpCodes.Ret));
                wrapCount++;
            }
            else foreach (var instruction in method.Body.Instructions)
            {
                var called = instruction.Operand as IMethod;
                if (called != null && called.FullName == "UnityEngine.Vector2 UnityEngine.GUIStyle::CalcSize(UnityEngine.GUIContent)")
                { instruction.OpCode = OpCodes.Call; instruction.Operand = measure; measureCount++; }
            }
        }
        Require(wrapCount == 5 && measureCount > 10, "Layout patch scope mismatch");
        foreach (var type in module.GetTypes()) foreach(var method in type.Methods)
            if(method.HasBody) method.Body.KeepOldMaxStack = true;
        Directory.CreateDirectory(Path.GetDirectoryName(output));
        module.Write(output);
        var check = ModuleDefMD.Load(output);
        Require(check.Types.Count == module.Types.Count, "Output type count mismatch");
        Require(check.Assembly.Name == "Assembly-CSharp", "Output identity changed");
        int verifiedBodies = 0;
        foreach (var type in check.GetTypes()) foreach (var method in type.Methods.Where(m=>m.HasBody))
        {
            var body = method.Body;
            foreach(var instruction in body.Instructions)
            {
                var target = instruction.Operand as Instruction;
                if(target != null) Require(body.Instructions.Contains(target), "Invalid output branch");
                var targets = instruction.Operand as IList<Instruction>;
                if(targets != null) foreach(var item in targets) Require(body.Instructions.Contains(item), "Invalid output switch");
            }
            verifiedBodies++;
        }
        if(args.Length > 4) File.WriteAllText(args[4], JsonSerializer.Serialize(new {
            source_sha256=sourceHash, sha256=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(output))).ToLowerInvariant(),
            helper_sha256=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(helperPath))).ToLowerInvariant(),
            translated_records=translated, direct_literals=direct, preserved_internal_key_records=deferred,
            translated_lookup_results=translatedResult, display_calls=displayCalls, wrapping_methods=wrapCount,
            measurement_calls=measureCount, output_method_bodies_verified=verifiedBodies
            , saved_bio_calls=savedBioCalls, saved_title_calls=savedTitleCalls, saved_description_calls=savedDescriptionCalls
            , tutorial_page_calls=tutorialPages, tutorial_header_calls=tutorialHeaders
        },new JsonSerializerOptions{WriteIndented=true}));
        Console.WriteLine("managed build passed: translated="+translated+", direct="+direct+", deferred="+deferred+", translated-result="+translatedResult+", display-calls="+displayCalls+", wrapping="+wrapCount+", size-calls="+measureCount);
    }
}
