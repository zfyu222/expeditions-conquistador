"""Mirror the validated public release using the workspace's configured Netdisk MCP."""
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[2]
async def main():
    public=json.loads((ROOT/'Repack/reports/github_release.json').read_text('utf-8'))
    assert public['status']=='passed' and public['anonymous_http_status']==200
    report=json.loads((ROOT/'Repack/reports/release_archive_validation.json').read_text('utf-8'))
    archive=ROOT/report['archive']
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==report['sha256']==public['sha256']
    config=json.loads((ROOT.parents[1]/'.mcp.json').read_text('utf-8-sig'))['mcpServers']['baidu-netdisk-local-uploader']
    env={**os.environ,**config.get('env',{})}
    params=StdioServerParameters(command=config['command'],args=config.get('args',[]),env=env)
    remote='/Hanhua/expeditions-conquistador'
    records=[]
    with open(os.devnull,'w') as errors:
        async with stdio_client(params,errlog=errors) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                listing=await session.list_tools()
                assert {'ensure_directory','delete_existing_patch_versions','upload_file'}.issubset({t.name for t in listing.tools})
                for tool,args in [('ensure_directory',{'remote_path':remote}),
                    ('delete_existing_patch_versions',{'remote_dir':remote,'game_name':'expeditions-conquistador'}),
                    ('upload_file',{'local_file_path':str(archive),'remote_path':remote})]:
                    result=await session.call_tool(tool,args)
                    data=getattr(result,'structuredContent',None)
                    if not data:
                        data=json.loads('\n'.join(c.text for c in result.content if getattr(c,'type','')=='text'))
                    # Only store publication results; no authentication or raw transport logs.
                    if data.get('status')!='success':
                        message=str(data.get('message','MCP tool failed'))
                        for value in env.values():
                            if isinstance(value,str) and len(value)>30 and value in message:message=message.replace(value,'[redacted]')
                        record={'tool':tool,'status':'error','message':message}
                        records.append(record)
                        (ROOT/'Repack/reports/baidu_release.json').write_text(json.dumps({'status':'error','steps':records},ensure_ascii=False,indent=2),encoding='utf-8')
                        raise RuntimeError(tool+': '+message)
                    record={'tool':tool,'status':'success'}
                    for key in ('path','remote_path','removed','created','file_size'):
                        if key in data:record[key]=data[key]
                    records.append(record)
                    print(json.dumps(record,ensure_ascii=False),flush=True)
    output={'status':'success','remote_path':records[-1].get('remote_path',remote+'/'+archive.name),
            'archive_sha256':report['sha256'],'steps':records}
    (ROOT/'Repack/reports/baidu_release.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    try:asyncio.run(main())
    except Exception:
        print('镜像未完成；详见 Repack/reports/baidu_release.json。后续删除及上传步骤未执行。',flush=True)
        sys.exit(1)
