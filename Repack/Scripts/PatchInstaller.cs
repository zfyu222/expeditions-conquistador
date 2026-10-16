using System;
using System.IO;
using System.Text;
using System.Linq;
using System.Diagnostics;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Web.Script.Serialization;

public class PatchFile
{
    public string game_path {get;set;}
    public string source_sha256 {get;set;}
    public string sha256 {get;set;}
    public string patch_path {get;set;}
    public string patch_sha256 {get;set;}
    public bool added {get;set;}
}
public class PatchManifest
{
    public string game_version {get;set;}
    public string translation_sha256 {get;set;}
    public string decoder_path {get;set;}
    public string decoder_sha256 {get;set;}
    public List<PatchFile> files {get;set;}
}
class PatchInstaller
{
    static string Hash(string path)
    {
        using(var hash=SHA256.Create()) using(var input=File.OpenRead(path))
            return BitConverter.ToString(hash.ComputeHash(input)).Replace("-","").ToLowerInvariant();
    }
    static string Under(string root,string relative)
    {
        if(Path.IsPathRooted(relative)) throw new Exception("补丁路径无效");
        string path=Path.GetFullPath(Path.Combine(root,relative.Replace('/',Path.DirectorySeparatorChar)));
        if(!path.StartsWith(root.TrimEnd(Path.DirectorySeparatorChar)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))
            throw new Exception("补丁路径越界");
        return path;
    }
    static void Require(bool value,string message) { if(!value) throw new Exception(message); }
    static string Q(string text) { return "\""+text+"\""; }
    static int Main(string[] args)
    {
        System.Console.OutputEncoding=Encoding.UTF8;
        bool interactive=args.Length==0;
        string root=Path.GetFullPath(AppDomain.CurrentDomain.BaseDirectory);
        bool uninstall=args.Contains("--uninstall");
        for(int i=0;i<args.Length;i++) if(args[i]=="--game-root" && i+1<args.Length) root=Path.GetFullPath(args[++i]);
        try
        {
            System.Console.WriteLine("《远征：征服者》子非鱼AI汉化补丁 v1.0");
            if(interactive)
            {
                System.Console.WriteLine("1：安装/检查汉化；2：还原原版；其他：退出");
                string answer=System.Console.ReadLine();
                if(answer!="1" && answer!="2") return 0;
                uninstall=answer=="2";
            }
            Require(File.Exists(Under(root,"Expeditions Conquistador.exe")),"请将安装程序和 ChinesePatch 文件夹解压到游戏根目录。");
            Require(Process.GetProcessesByName("Expeditions Conquistador").Length==0,"请先退出游戏，再运行安装程序。");
            var json=new JavaScriptSerializer(); json.MaxJsonLength=5000000;
            var manifest=json.Deserialize<PatchManifest>(File.ReadAllText(Under(root,"ChinesePatch/patch_manifest.json"),Encoding.UTF8));
            Require(manifest.files.Count==7,"补丁清单不完整");
            string backupRoot=Under(root,"ChinesePatch/Backup");
            if(uninstall)
            {
                foreach(var file in manifest.files)
                {
                    string installed=Under(root,file.game_path);
                    if(File.Exists(installed)) Require(Hash(installed)==file.sha256 || Hash(installed)==file.source_sha256,"文件已被其他补丁修改，停止还原："+file.game_path);
                    if(!file.added) Require(File.Exists(Under(backupRoot,file.game_path)) && Hash(Under(backupRoot,file.game_path))==file.source_sha256,"原版备份缺失："+file.game_path);
                }
                foreach(var file in manifest.files)
                {
                    string installed=Under(root,file.game_path);
                    if(file.added) { if(File.Exists(installed)) File.Delete(installed); }
                    else File.Copy(Under(backupRoot,file.game_path),installed,true);
                    System.Console.WriteLine("已还原："+file.game_path);
                }
                System.Console.WriteLine("原版已还原。ChinesePatch/Backup 中的备份仍然保留。");
            }
            else
            {
                string decoder=Under(root,manifest.decoder_path);
                Require(File.Exists(decoder) && Hash(decoder)==manifest.decoder_sha256,"差分解码器缺失或损坏");
                foreach(var file in manifest.files)
                {
                    string installed=Under(root,file.game_path), patch=Under(root,file.patch_path);
                    Require(File.Exists(patch) && Hash(patch)==file.patch_sha256,"差分载荷损坏："+file.patch_path);
                    if(File.Exists(installed))
                    {
                        string current=Hash(installed);
                        Require(current==file.source_sha256 || current==file.sha256,"不支持的游戏版本或文件已被修改："+file.game_path);
                        if(current==file.sha256 && !file.added)
                            Require(File.Exists(Under(backupRoot,file.game_path)) && Hash(Under(backupRoot,file.game_path))==file.source_sha256,"已有汉化但缺少原版备份，请先验证游戏文件："+file.game_path);
                    }
                    else Require(file.added,"游戏文件缺失："+file.game_path);
                }
                string staging=Under(root,"ChinesePatch/Staging/"+Guid.NewGuid().ToString("N"));
                var prepared=new Dictionary<PatchFile,string>();
                foreach(var file in manifest.files)
                {
                    string installed=Under(root,file.game_path), patch=Under(root,file.patch_path), output=Under(staging,file.game_path);
                    Directory.CreateDirectory(Path.GetDirectoryName(output));
                    if(file.added) File.Copy(patch,output);
                    else if(Hash(installed)==file.sha256) File.Copy(installed,output);
                    else
                    {
                        var start=new ProcessStartInfo(decoder,"-d -s "+Q(installed)+" "+Q(patch)+" "+Q(output));
                        start.UseShellExecute=false; start.CreateNoWindow=true;
                        using(var process=Process.Start(start)) { process.WaitForExit(); Require(process.ExitCode==0,"差分解码失败："+file.game_path); }
                    }
                    Require(Hash(output)==file.sha256,"解码后的文件校验失败："+file.game_path);
                    prepared.Add(file,output);
                    System.Console.WriteLine("校验通过："+file.game_path);
                }
                foreach(var file in manifest.files.Where(f=>!f.added))
                {
                    string backup=Under(backupRoot,file.game_path);
                    if(!File.Exists(backup))
                    { Directory.CreateDirectory(Path.GetDirectoryName(backup)); File.Copy(Under(root,file.game_path),backup); }
                    Require(Hash(backup)==file.source_sha256,"原版备份校验失败："+file.game_path);
                }
                var copied=new List<PatchFile>();
                try
                {
                    foreach(var file in manifest.files)
                    {
                        string installed=Under(root,file.game_path);
                        Directory.CreateDirectory(Path.GetDirectoryName(installed));
                        File.Copy(prepared[file],installed,true); copied.Add(file);
                        Require(Hash(installed)==file.sha256,"安装校验失败："+file.game_path);
                    }
                }
                catch
                {
                    foreach(var file in copied)
                    {
                        string installed=Under(root,file.game_path);
                        if(file.added) { if(File.Exists(installed)) File.Delete(installed); }
                        else File.Copy(Under(backupRoot,file.game_path),installed,true);
                    }
                    throw;
                }
                foreach(var output in prepared.Values) File.Delete(output);
                File.WriteAllText(Under(root,"ChinesePatch/installation_log.json"),json.Serialize(new {
                    status="passed",utc=DateTime.UtcNow.ToString("O"),game_version=manifest.game_version,
                    translation_sha256=manifest.translation_sha256,files=manifest.files.Select(f=>new{game_path=f.game_path,sha256=Hash(Under(root,f.game_path))}).ToArray()
                }),Encoding.UTF8);
                System.Console.WriteLine("汉化安装完成。请在游戏中选择 English/英语。原版备份位于 ChinesePatch/Backup。");
            }
            if(interactive) { System.Console.WriteLine("按回车退出。"); System.Console.ReadLine(); }
            return 0;
        }
        catch(Exception e)
        {
            System.Console.Error.WriteLine("操作停止："+e.Message);
            if(interactive) System.Console.ReadLine();
            return 1;
        }
    }
}
