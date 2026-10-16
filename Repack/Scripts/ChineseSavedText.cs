using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;
namespace Zfy.Localization { public static partial class SavedDisplay {
        static string SavedLookup(Dictionary<string,string> map, string text)
        {
            if (text == null) return text;
            string result;
            return map.TryGetValue(text, out result) ? result : text;
        }
        public static string SavedBio(string text) { return SavedLookup(SavedBios, text); }
        public static string SavedTitle(string text)
        {
            string result = SavedLookup(SavedTitles, text);
            if (result != text || text == null) return result;
            const string chart = "Chart the ";
            if (text.StartsWith(chart, StringComparison.Ordinal))
                return SavedLookup(SavedFragments,chart)+SavedLookup(SavedFragments,text.Substring(chart.Length));
            return text;
        }
        public static string SavedDescription(string text)
        {
            string result = SavedLookup(SavedDescriptions, text);
            if (result != text || text == null) return result;
            Match cairns = Regex.Match(text, @"\ADiscovered ([0-9]+) out of ([0-9]+) cairns\z");
            if (cairns.Success) return SavedLookup(SavedFragments,"Discovered ")+cairns.Groups[1].Value
                +SavedLookup(SavedFragments," out of ")+cairns.Groups[2].Value+SavedLookup(SavedFragments," cairns");
            return text;
        }
}}
