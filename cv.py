
from langgraph.graph import StateGraph, END
from typing import TypedDict
import re
import getpass
import os
os.environ["DEEPSEEK_API_KEY"] = "sk-185ccf2f63564c93bb45b5bee4c24d08"
from langchain_deepseek import ChatDeepSeek
llm = ChatDeepSeek(model="deepseek-chat")
class CVState(TypedDict):
    file_path: str
    cv_text: str
    parsed_data: dict
    user_query: str
    mes: str
    already_ask: bool
    ask_more: bool


import fitz

def extract_pdf_text(file_path: str) -> str:
    cv_text=''
    with fitz.open(file_path) as doc:
        for page in doc:
            cv_text+= page.get_text()
    return cv_text

def receive_cv(state: CVState) -> CVState:
    if 'cv_text' in state:
        del state['file_path']
        return state
    file_path=state['file_path']
    cv_text= extract_pdf_text(file_path)
    return {**state, 'cv_text': cv_text}

def parse_cv(state: CVState) -> CVState:
    if 'parse_data' in state:
        return state
    if 'file_path' not in state or not state['file_path']:
        return state
    prompt = f"""
    Đây là nội dung CV của ứng viên. 
    1. Hãy trích xuất những thông tin quan trọng nhất(tên, liên hệ, học vấn, kinh nghiệm, năng lực,....)
    Nội dung CV:\n\n{state["cv_text"]}
    2.Từ những thông tin trên, gợi ý vị trí ứng viên có thể tham gia(2 vị trí)
    3. Đưa ra 2 điểm mạnh và 2 điểm yếu cho từng vị trí
    4. Dựa vào đó, hãy đưa ra quyết định ngắn gọn cho doanh nghiệp xem có nên tuyển hay không
    """
    response = llm.invoke(prompt)
    print(response.content)
    return {**state, "parsed_data": response.content}

def cont(state: dict):
    if state.get('user_query'):
        state['already_ask'] = True
        return 'qna'
    elif state.get('already_ask'):
        return END
    return END
    
def qna(state:dict):
    query= state['user_query']
    prompt_4 = f"""
    Trả lời câu hỏi sau liên quan tới thông tin CV một cách ngắn gọn
    Câu hỏi: {query}, dựa vào dữ liệu đã trích xuất
    Thông tin CV đã được lưu sẵn, chỉ cần trả lời ngắn gọn
    """
    ans=llm.invoke(prompt_4)
    state['mes'] = ans
    state['ask_more'] = False
    print(ans.content)
    return state

def cont_2(state: CVState):
    if state['ask_more'] == True:
        return 'continue'
    else:
        return 'stop'
    
builder=StateGraph(CVState)
    
builder.add_node("ReceiveCV", receive_cv)
builder.add_node("ParseCV", parse_cv)
builder.add_node('QNA',qna)

builder.set_entry_point("ReceiveCV")
builder.add_edge("ReceiveCV", "ParseCV")
builder.add_conditional_edges('ParseCV', cont,{'qna': 'QNA', END:END})
builder.add_conditional_edges('QNA', cont_2,{'continue': 'QNA', 'stop': END} )
graph=builder.compile()