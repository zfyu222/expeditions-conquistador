using System;
using System.Collections.Generic;
using UnityEngine;
namespace Zfy.Localization
{
    public static partial class ChineseLayout
    {
        static readonly Dictionary<string,Vector2> TutorialScroll = new Dictionary<string,Vector2>();
        static Texture2D tutorialSolid;
        static Texture2D TutorialSolid
        {
            get
            {
                if (tutorialSolid == null)
                {
                    tutorialSolid = new Texture2D(1,1);
                    tutorialSolid.SetPixel(0,0,Color.white);
                    tutorialSolid.Apply();
                    tutorialSolid.hideFlags = HideFlags.HideAndDontSave;
                }
                return tutorialSolid;
            }
        }
        public static void DrawTutorialPage(Rect area, Texture image, GUIStyle sourceStyle)
        {
            string caption;
            if (image == null || !TutorialCaptions.TryGetValue(image.name, out caption))
            { GUI.DrawTexture(area,image); return; }
            // Keep the full original image and aspect ratio; add a separate Chinese explanation.
            float previewHeight = area.height * 0.8f;
            float previewWidth = previewHeight * image.width / image.height;
            GUI.DrawTexture(new Rect(area.x+(area.width-previewWidth)/2f,area.y,previewWidth,previewHeight),image);
            Rect footer = new Rect(area.x+8f,area.y+previewHeight+4f,area.width-16f,area.height-previewHeight-8f);
            Color previous = GUI.color;
            GUI.color = new Color(0f,0f,0f,0.9f);
            GUI.DrawTexture(footer,TutorialSolid);
            GUI.color = previous;
            GUIStyle style = new GUIStyle(sourceStyle);
            style.alignment = TextAnchor.UpperLeft;
            style.wordWrap = false;
            style.fontSize = 16;
            style.normal.textColor = Color.white;
            int height;
            string text = Wrap(caption,style,0,(int)footer.width-30,out height);
            Vector2 scroll;
            if (!TutorialScroll.TryGetValue(image.name,out scroll)) scroll=Vector2.zero;
            scroll=GUI.BeginScrollView(footer,scroll,new Rect(0f,0f,footer.width-20f,Math.Max(height+8f,footer.height)));
            GUI.Label(new Rect(4f,4f,footer.width-28f,height+4f),text,style);
            GUI.EndScrollView();
            TutorialScroll[image.name]=scroll;
        }
        public static void DrawTutorialHeader(Rect area, Texture image, GUIStyle sourceStyle)
        {
            GUI.DrawTexture(area,image);
            string title;
            if (!TutorialCaptions.TryGetValue("Tutorials",out title)) return;
            Rect label=new Rect(area.x+110f,area.y,area.width-110f,area.height);
            Color previous=GUI.color;
            GUI.color=new Color(0f,0f,0f,1f);
            GUI.DrawTexture(label,TutorialSolid);
            GUI.color=previous;
            GUIStyle style=new GUIStyle(sourceStyle);
            style.alignment=TextAnchor.MiddleCenter;
            style.fontSize=18;
            style.normal.textColor=Color.white;
            GUI.Label(label,title,style);
        }
    }
}
