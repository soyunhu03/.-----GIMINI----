print('이 프로그램은 구글의 AI GEMINI로 만들어 졌습니다.')
print('과도한 API 사용에 대해서는 책임지지 않습니다.')
print('해당 프로그램 사용으로 인한 피해는 전적으로 사용자에게 있습니다.(예, 카카오톡 계정 정지, API 비용 청구 등)')
동의 = input('위 내용을 숙지하였으며 이에 동의하십니까? (동의하면 엔터를 입력하십시오)')
import time
import sys
import win32con
import win32api
import win32gui
import ctypes
import pyautogui
import pyperclip
import google.generativeai as genai
import re
import os

# ==========================================
# [전역 변수] 사용자 입력으로 채워질 예정
# ==========================================
GEMINI_API_KEY = ""
KAKAO_CHATROOM_NAME = ""
MY_NAME = ""
SYSTEM_PROMPT = ""
model = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_user_config():
    """사용자로부터 실행에 필요한 정보를 입력받습니다."""
    global GEMINI_API_KEY, KAKAO_CHATROOM_NAME, MY_NAME, SYSTEM_PROMPT
    
    clear_screen()
    print("==============================================")
    print("   🤖 GIMINI : 카카오톡 AI 자동응답 봇")
    print("==============================================")
    
    while not GEMINI_API_KEY:
        GEMINI_API_KEY = input("1. Google Gemini API Key를 입력하세요: ").strip()
    
    while not KAKAO_CHATROOM_NAME:
        KAKAO_CHATROOM_NAME = input("2. 작동시킬 카카오톡 채팅방 이름을 정확히 입력하세요: ").strip()
        
    while not MY_NAME:
        MY_NAME = input("3. 본인의 카카오톡 프로필 이름(내가 쓴 글 인식용)을 입력하세요: ").strip()
        
    print("\n4. AI에게 부여할 역할이나 말투를 설정하세요.")
    print("   (예: '친절한 비서처럼 존댓말로 대답해', '해적 말투로 대답해')")
    print("   [입력하지 않고 엔터를 치면 기본 설정으로 동작합니다]")
    SYSTEM_PROMPT = input("   입력 > ").strip()
    
    print("\n----------------------------------------------")
    print(f"API KEY: {GEMINI_API_KEY[:5]}..." + "*"*10)
    print(f"채팅방:  {KAKAO_CHATROOM_NAME}")
    print(f"내 이름: {MY_NAME}")
    print(f"말투:    {SYSTEM_PROMPT if SYSTEM_PROMPT else '기본'}")
    print("----------------------------------------------")
    input("설정이 완료되었습니다. 엔터를 누르면 GIMINI를 시작합니다...")

def select_best_model():
    """사용 가능한 모델을 순회하며 할당량이 남은 최적의 모델을 자동으로 선택합니다."""
    global model
    print("\n🤖 GIMINI 연결 테스트 중...")
    
    # 입력받은 키로 설정
    genai.configure(api_key=GEMINI_API_KEY)
    
    try:
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as e:
            print(f"\n[⛔ 치명적 오류] API 키가 올바르지 않거나 권한이 없습니다.\n에러: {e}")
            return False
        
        if not available_models:
            print("\n[❌ 실패] 사용 가능한 모델 목록을 가져올 수 없습니다.")
            return False

        preferences = ['flash-lite', 'gemini-2.5-flash', 'gemini-2.0-flash', 'flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']
        
        sorted_candidates = []
        for pref in preferences:
            for name in available_models:
                if pref in name and name not in sorted_candidates:
                    sorted_candidates.append(name)
        for name in available_models:
            if name not in sorted_candidates:
                sorted_candidates.append(name)

        for candidate_name in sorted_candidates:
            print(f"   ➡️ 시도 중: {candidate_name} ...", end="")
            try:
                temp_model = genai.GenerativeModel(candidate_name)
                temp_model.generate_content("Hi")
                print(" [성공] ✅")
                model = temp_model
                print(f"   ✨ 최종 선택된 모델: {candidate_name}")
                return True
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    print(" [할당량 초과] ⚠️")
                else:
                    print(f" [실패] ❌")
                continue
                
        print("\n[❌ 실패] 사용 가능한 모든 모델이 연결할 수 없습니다.")
        return False

    except Exception as e:
        print(f"\n\n[⛔ 오류] 초기화 중 예외 발생: {e}")
        return False

def get_gemini_response(user_question):
    """설정된 프롬프트와 함께 질문을 보냅니다."""
    try:
        # 사용자가 설정한 문장 + 실제 질문 결합
        if SYSTEM_PROMPT:
            full_prompt = f"{SYSTEM_PROMPT}\n\n[사용자 질문]: {user_question}"
        else:
            full_prompt = user_question
            
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "오류가 발생했습니다."

def open_chatroom(chatroom_name):
    try:
        hwnd = win32gui.FindWindow(None, chatroom_name)
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            return True
        else:
            return False
    except Exception:
        try:
            hwnd = win32gui.FindWindow(None, chatroom_name)
            if hwnd:
                pyautogui.press('alt')
                win32gui.SetForegroundWindow(hwnd)
                return True
        except:
            pass
        return False

def copy_chat_content():
    try:
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.05)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.05)
        pyautogui.press('down')
        return pyperclip.paste()
    except Exception:
        return ""

def send_message(message):
    pyperclip.copy(message)
    time.sleep(0.5) 
    
    # 창 활성화 시도 및 실패 시 로그 출력 (수정됨)
    if not open_chatroom(KAKAO_CHATROOM_NAME):
        print(f"\n⚠️ 전송 실패: '{KAKAO_CHATROOM_NAME}' 창을 찾을 수 없습니다.")
        return

    # 창이 활성화된 후 안정화될 때까지 잠시 대기 (수정됨: 0.5초 추가)
    time.sleep(0.5)

    pyautogui.press('enter') # 포커스 확보
    time.sleep(0.1)
    
    pyautogui.keyDown('ctrl')
    time.sleep(0.1) 
    pyautogui.press('v')
    time.sleep(0.1) 
    pyautogui.keyUp('ctrl')
    
    time.sleep(0.5) 
    pyautogui.press('enter')
    time.sleep(0.2)

    # 센터 클릭으로 포커스 이동 (다음 인식 준비)
    try:
        hwnd = win32gui.FindWindow(None, KAKAO_CHATROOM_NAME)
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            center_x = (rect[0] + rect[2]) // 2
            center_y = (rect[1] + rect[3]) // 2
            pyautogui.click(center_x, center_y)
    except:
        pass

def parse_command(line):
    match = re.search(r'\[.+?\] \[.+?\] (.+)', line)
    if match:
        content = match.group(1).strip()
        if content.lower().startswith("@gemini"):
            return content[7:].strip()
    return None

def main():
    # 1. 사용자 설정 입력 받기
    get_user_config()
    
    # 2. 모델 연결 및 검증
    if not select_best_model():
        print("프로그램을 종료합니다. (엔터를 누르면 닫힙니다)")
        input()
        sys.exit(1)

    print(f"\n[{KAKAO_CHATROOM_NAME}] GIMINI 작동 시작... (중지하려면 Ctrl+C)")
    print("안내: 채팅방 창을 열어두셔야 합니다.")
    
    last_message = ""
    is_first_run = True

    try:
        while True:
            if not open_chatroom(KAKAO_CHATROOM_NAME):
                print(f"⚠️ '{KAKAO_CHATROOM_NAME}' 채팅방을 찾을 수 없습니다. 창을 열어주세요.")
                time.sleep(5)
                continue

            # 첫 실행 안내
            if is_first_run:
                print("👋 GIMINI 시작 안내 메시지 전송 중...")
                welcome_msg = f"GIMINI 봇이 연결되었습니다!\n설정된 역할: {SYSTEM_PROMPT if SYSTEM_PROMPT else '기본'}\n@gemini (질문) 형식으로 물어보세요."
                send_message(welcome_msg)
                is_first_run = False
                time.sleep(2)
                full_chat = copy_chat_content()
                if full_chat:
                    lines = full_chat.strip().split('\n')
                    if lines: last_message = lines[-1]
                continue

            full_chat = copy_chat_content()
            if not full_chat:
                time.sleep(1)
                continue

            lines = full_chat.strip().split('\n')
            if not lines: continue
            
            recent_line = lines[-1]

            if recent_line != last_message:
                if "[AI]" in recent_line:
                    last_message = recent_line
                    time.sleep(1)
                    continue

                if MY_NAME in recent_line and "@gemini" not in recent_line.lower():
                    last_message = recent_line
                    time.sleep(1)
                    continue

                print(f"📩 감지됨: {recent_line}")
                
                user_question = parse_command(recent_line)
                
                if user_question:
                    print(f"❓ 질문 인식: {user_question}")
                    reply = get_gemini_response(user_question)
                    final_reply = f"[AI] {reply}"
                    send_message(final_reply)
                
                last_message = recent_line

            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nGIMINI를 종료합니다.")
    except Exception as e:
        print(f"\n[오류 발생] {e}")
        input("엔터를 누르면 종료합니다.")

if __name__ == "__main__":
    main()