import os, json, sqlite3
from pathlib import Path
from datetime import date
import requests, fitz, streamlit as st
from dotenv import load_dotenv
load_dotenv()
st.set_page_config(page_title='ResearchLens 科研解读',page_icon='🔬',layout='wide')
DB=Path(__file__).parent/'papers.db'
with sqlite3.connect(DB) as con:
 con.execute('CREATE TABLE IF NOT EXISTS papers (id TEXT PRIMARY KEY, raw TEXT)')
def save(p):
 with sqlite3.connect(DB) as con: con.execute('INSERT OR REPLACE INTO papers VALUES (?,?)',(p['id'],json.dumps(p,ensure_ascii=False)))
def saved():
 with sqlite3.connect(DB) as con: return [json.loads(x[0]) for x in con.execute('SELECT raw FROM papers').fetchall()]
def abstract(inv):
 return ' '.join(w for _,w in sorted((i,w) for w,positions in (inv or {}).items() for i in positions))
def search(q,dt,n,key):
 params={'search':q,'per_page':n,'sort':'publication_date:desc','filter':f'from_publication_date:{dt}'}
 if key: params['api_key']=key
 r=requests.get('https://api.openalex.org/works',params=params,timeout=30);r.raise_for_status()
 return [{'id':w['id'],'title':w.get('display_name') or '无标题','date':w.get('publication_date') or '', 'doi':w.get('doi') or '', 'abstract':abstract(w.get('abstract_inverted_index')), 'authors':[a.get('author',{}).get('display_name','') for a in w.get('authorships',[])][:5], 'url':w['id'],'full_text':'','type':w.get('type','unknown')} for w in r.json().get('results',[])]
def content_of(p):
 return ('上传 PDF 全文',p['full_text']) if p.get('full_text') else ('OpenAlex 摘要',p.get('abstract',''))
def interpret(p,audience,question,key,model):
 source,content=content_of(p)
 if not content: return '无摘要或全文，不能生成有依据的解读。'
 if not key:
  return f'''### {p['title']}\n\n**当前材料：** {source}\n\n**原文摘录（非 AI 结论）：**\n\n> {content[:1500]}\n\n**阅读检查：** 研究问题是什么？研究设计和样本量是什么？结论有哪些限制？\n\n⚠️ 这是无模型模式的原文摘录与阅读提示，不是自动科研解读。配置 OpenAI API Key 后启用真正的分层解读和问答。'''
 from openai import OpenAI
 system='你是严谨的跨学科论文解读Agent。只依据提供材料回答，不能编造论文事实、数据、DOI、页码。重要结论附上材料中的短句证据。区分事实、推断、未知。摘要材料必须标明仅依据摘要，不能声称审阅全文。针对受众调整术语和深度。用中文回答。'
 prompt=f'受众：{audience}\n任务：{question}\n标题：{p["title"]}\nDOI：{p.get("doi")}\n来源：{source}\n材料（最多45000字符）：\n{content[:45000]}'
 resp=OpenAI(api_key=key,timeout=60).chat.completions.create(model=model,temperature=0.2,messages=[{'role':'system','content':system},{'role':'user','content':prompt}])
 return resp.choices[0].message.content or '模型未返回内容'
st.title('🔬 ResearchLens · 科研论文解读 Agent')
st.caption('真实跨学科论文检索 · PDF 阅读 · 大众/学生/研究者三层解读 · 基于材料的追问')
with st.sidebar:
 st.header('设置')
 audience=st.selectbox('解读对象',['大众科普','科研入门','专业科研'])
 oa_key=st.text_input('OpenAlex API Key',value=os.getenv('OPENALEX_API_KEY',''),type='password')
 ai_key=st.text_input('OpenAI API Key（可选）',value=os.getenv('OPENAI_API_KEY',''),type='password')
 model=st.text_input('模型',value=os.getenv('OPENAI_MODEL','gpt-4.1-mini'))
 st.info('无 OpenAI Key 仍可检索、保存、阅读论文。AI 解读和追问需 Key。')
t1,t2,t3=st.tabs(['🔎 搜索最新论文','📄 上传 PDF','📚 已保存论文'])
with t1:
 with st.form('search'):
  a,b,c=st.columns([4,2,1]);q=a.text_input('研究主题',value='artificial intelligence scientific discovery');dt=b.date_input('最早发表日期',value=date(2025,1,1));n=c.number_input('数量',1,50,8)
  go=st.form_submit_button('检索真实论文',type='primary')
 if go:
  try:
   with st.spinner('检索 OpenAlex...'): st.session_state.results=search(q,str(dt),int(n),oa_key)
  except Exception as e: st.error(f'检索失败：{e}；请检查网络和 OpenAlex API Key。')
 for i,p in enumerate(st.session_state.get('results',[])):
  with st.container(border=True):
   st.markdown(f'**{i+1}. {p["title"]}**');st.caption(f'{p["date"]} · {p["type"]} · {", ".join(p["authors"][:3])}')
   st.write((p['abstract'][:350]+'…') if len(p['abstract'])>350 else (p['abstract'] or '无摘要'))
   x,y,z=st.columns([1,1,3])
   if x.button('选择解读',key=f's{i}'): st.session_state.paper=p;st.session_state.pop('analysis',None);st.success('已选择，请向下滚动')
   if y.button('保存',key=f'v{i}'): save(p);st.success('已保存')
   if p['url']: z.link_button('论文来源',p['url'])
with t2:
 f=st.file_uploader('上传文字型 PDF（扫描版暂不支持）',type='pdf')
 if f and st.button('解析并选择 PDF'):
  try:
   doc=fitz.open(stream=f.getvalue(),filetype='pdf');txt='\n'.join(page.get_text(sort=True) for page in doc)
   if not txt.strip(): st.error('未提取到文字，请上传非扫描 PDF')
   else:
    st.session_state.paper={'id':'upload:'+f.name,'title':f.name,'date':'','doi':'','abstract':'','authors':[],'url':'','full_text':txt}
    st.session_state.pop('analysis',None);st.success(f'已解析 {len(doc)} 页，{len(txt)} 字符')
  except Exception as e: st.error(f'PDF 解析失败：{e}')
with t3:
 items=saved();st.caption(f'已保存 {len(items)} 篇')
 for i,p in enumerate(items):
  a,b=st.columns([5,1]);a.write(f'{p["title"]} · {p["date"]}')
  if b.button('选择',key=f'lib{i}'):st.session_state.paper=p;st.session_state.pop('analysis',None)
st.divider();st.subheader('🧠 分层解读与追问')
p=st.session_state.get('paper')
if p:
 source,body=content_of(p);st.markdown(f'**{p["title"]}**');st.caption(f'证据材料：{source}，{len(body)} 字符；受众：{audience}')
 if p.get('url'):st.markdown(f'[查看原始论文记录]({p["url"]})')
 if not body:st.warning('此论文没有可用摘要。请上传 PDF 后解读。')
 if st.button('生成分层解读',type='primary',disabled=not bool(body)):
  try:
   with st.spinner('正在分析论文...'):st.session_state.analysis=interpret(p,audience,'解读研究问题、研究方法、主要结果、证据限制、尚未证明什么、进一步阅读问题。必须引用材料中的短句。',ai_key,model)
  except Exception as e:st.error(f'解读失败：{e}')
 if st.session_state.get('analysis'):
  st.markdown(st.session_state.analysis)
  st.download_button('导出 Markdown',st.session_state.analysis,file_name='paper_analysis.md')
 question=st.text_area('针对当前论文追问',placeholder='例如：研究方法有哪些局限？')
 if st.button('提问',disabled=not bool(body and ai_key and question.strip())):
  try:
   with st.spinner('正在根据材料回答...'):st.markdown(interpret(p,audience,question,ai_key,model))
  except Exception as e:st.error(f'回答失败：{e}')
else:st.info('请先检索并选择论文，或上传 PDF。')
st.caption('MVP 限制：当前为单篇文献材料问答，不包含多篇向量 RAG、自动更新或严格证据分级；模型输出仍需人工核验。')
