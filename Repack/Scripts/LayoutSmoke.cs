using System;
using System.Text;
using Zfy.Localization;
class LayoutSmoke
{
    static void Check(string input,string expected)
    {
        var chunks=ChineseLayout.BuildChunks(input,null,null,null,null);
        var result=new StringBuilder();
        foreach(var chunk in chunks) result.Append(chunk.text);
        if(result.ToString()!=expected) throw new Exception("Text preservation failed: "+input);
        foreach(var chunk in chunks)
            if(chunk.text.Length>0 && "，。！？；：、）］】》」』”’％".IndexOf(chunk.text[0])>=0)
                throw new Exception("Closing punctuation starts a chunk: "+chunk.text);
    }
    static void Main()
    {
        Check("你好，世界！","你好，世界！");
        Check("你说：“跟我来。”","你说：“跟我来。”");
        Check("Don Pedro de Alvarado","Don Pedro de Alvarado");
        Check("兵力 150，粮食 20。","兵力 150，粮食 20。");
        Check("*勇敢*的/战士/和$选项$。","勇敢的战士和选项。");
        Check("第一段。\n\n第二段。","第一段。\n\n第二段。");
        Check(" uses Cure on "," uses Cure on ");
        Check("（说明）与Latin混排。","（说明）与Latin混排。");
        System.Console.WriteLine("Layout token smoke tests: 8 passed");
    }
}
