using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

namespace Zfy.Localization
{
    public sealed class ChineseChunk
    {
        public GUIStyle guistyle;
        public string text;
        public ChineseChunk(GUIStyle style, string value) { guistyle = style; text = value; }
    }
    // Called by the statically patched game assembly; no loader or translation service.
    public static partial class ChineseLayout
    {
        static bool Cjk(char c)
        {
            return (c >= '\u2e80' && c <= '\u9fff') || (c >= '\uf900' && c <= '\ufaff')
                || (c >= '\ufe30' && c <= '\uffef') || c == '\u2014' || c == '\u2026';
        }
        static bool Closing(char c) { return "，。！？；：、）］】》」』”’％…".IndexOf(c) >= 0; }
        static bool Opening(char c) { return "（［【《「『“‘".IndexOf(c) >= 0; }

        static GUIContent LocalizeContent(GUIContent source)
        {
            if (source == null) return source;
            string text = Localize(source.text);
            if (text == source.text) return source;
            return new GUIContent(text, source.image, source.tooltip);
        }
        public static string UseDisplayText(string originalResult, string translated) { return translated; }
        public static bool Button(Rect r, GUIContent c, GUIStyle s) { return GUI.Button(r, LocalizeContent(c), s); }
        public static bool Button(Rect r, string c, GUIStyle s) { return GUI.Button(r, Localize(c), s); }
        public static bool Button(Rect r, GUIContent c) { return GUI.Button(r, LocalizeContent(c)); }
        public static bool Button(Rect r, string c) { return GUI.Button(r, Localize(c)); }
        public static void Label(Rect r, GUIContent c, GUIStyle s) { GUI.Label(r, LocalizeContent(c), s); }
        public static void Label(Rect r, string c, GUIStyle s) { GUI.Label(r, Localize(c), s); }
        public static void Label(Rect r, GUIContent c) { GUI.Label(r, LocalizeContent(c)); }
        public static void Label(Rect r, string c) { GUI.Label(r, Localize(c)); }

        static List<string> Tokens(string text)
        {
            var result = new List<string>();
            var word = new StringBuilder();
            for (int i = 0; i < text.Length; i++)
            {
                char c = text[i];
                if (c == '\r') continue;
                if (c == '\n')
                {
                    if (word.Length > 0) { result.Add(word.ToString()); word.Length = 0; }
                    int count = 1;
                    while (i + 1 < text.Length && (text[i + 1] == '\r' || text[i + 1] == '\n'))
                        if (text[++i] == '\n') count++;
                    result.Add(new string('\n', count));
                }
                else if (char.IsWhiteSpace(c))
                {
                    if (word.Length > 0) { result.Add(word.ToString() + c); word.Length = 0; }
                    else if (result.Count > 0) result[result.Count - 1] += c;
                    else word.Append(c);
                }
                else if (Closing(c))
                {
                    if (word.Length > 0) { word.Append(c); result.Add(word.ToString()); word.Length = 0; }
                    else if (result.Count > 0 && !result[result.Count-1].EndsWith("\n")) result[result.Count - 1] += c;
                    else word.Append(c);
                }
                else if (Opening(c))
                {
                    if (word.Length > 0) { result.Add(word.ToString()); word.Length = 0; }
                    word.Append(c);
                }
                else if (Cjk(c))
                {
                    if (word.Length > 0 && !Opening(word[word.Length - 1]))
                    { result.Add(word.ToString()); word.Length = 0; }
                    word.Append(c); result.Add(word.ToString()); word.Length = 0;
                }
                else word.Append(c);
            }
            if (word.Length > 0) result.Add(word.ToString());
            return result;
        }

        static void AddChunks(List<ChineseChunk> chunks, StringBuilder buffer, GUIStyle style)
        {
            if (buffer.Length == 0) return;
            foreach (string token in Tokens(buffer.ToString())) chunks.Add(new ChineseChunk(style, token));
            buffer.Length = 0;
        }

        public static ChineseChunk[] BuildChunks(string text, GUIStyle normal, GUIStyle italic, GUIStyle bold, GUIStyle color)
        {
            var chunks = new List<ChineseChunk>();
            var buffer = new StringBuilder();
            GUIStyle active = normal;
            for (int i = 0; i < text.Length; i++)
            {
                char c = text[i];
                if (c == '/' || c == '*' || c == '$')
                {
                    AddChunks(chunks, buffer, active);
                    GUIStyle selected = c == '/' ? italic : c == '*' ? bold : color;
                    active = active == selected ? normal : selected;
                }
                else buffer.Append(c);
            }
            AddChunks(chunks, buffer, active);
            return chunks.ToArray();
        }

        public static Vector2 Measure(GUIStyle style, GUIContent content)
        {
            string text = content.text;
            if (!string.IsNullOrEmpty(text) && text.Trim('\n').Length == 0)
            {
                float line = style.CalcSize(new GUIContent("国Ag")).y;
                return new Vector2(1048576f, Math.Max(0, text.Length - 1) * line);
            }
            return style.CalcSize(content);
        }

        public static string Wrap(string text, GUIStyle style, int initialX, int finalX, out int height)
        {
            int width;
            return Wrap(text, style, initialX, finalX, out height, out width);
        }

        public static string Wrap(string text, GUIStyle style, int initialX, int finalX, out int height, out int linewidth)
        {
            int available = Math.Max(1, finalX - initialX);
            var output = new StringBuilder();
            var line = new StringBuilder();
            int lines = 1;
            foreach (string token in Tokens(text ?? ""))
            {
                if (token.StartsWith("\n"))
                {
                    output.Append(line); output.Append(token); line.Length = 0; lines += token.Length;
                    continue;
                }
                if (line.Length > 0 && style.CalcSize(new GUIContent(line.ToString() + token)).x > available)
                { output.Append(line); output.Append('\n'); line.Length = 0; lines++; }
                if (style.CalcSize(new GUIContent(token)).x > available)
                {
                    foreach (char c in token)
                    {
                        if (line.Length > 0 && style.CalcSize(new GUIContent(line.ToString() + c)).x > available)
                        { output.Append(line); output.Append('\n'); line.Length = 0; lines++; }
                        line.Append(c);
                    }
                }
                else line.Append(token);
            }
            linewidth = (int)Math.Ceiling(style.CalcSize(new GUIContent(line.ToString())).x);
            output.Append(line);
            height = lines * (int)Math.Ceiling(style.CalcSize(new GUIContent("国Ag")).y);
            return output.ToString();
        }
    }
}
