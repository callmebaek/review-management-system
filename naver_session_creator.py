"""
네이버 세션 생성기 (Naver Session Creator)
리뷰 관리 시스템 - 네이버 플레이스 세션 자동 생성 도구
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class NaverSessionCreator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("네이버 세션 생성기 v1.0")
        self.window.geometry("500x600")
        self.window.resizable(False, False)
        
        # API 설정
        self.api_url = "https://review-management-system-5bc2651ced45.herokuapp.com"
        
        # 상태 변수
        self.is_processing = False
        self.driver = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        # 헤더
        header_frame = tk.Frame(self.window, bg="#4F46E5", height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🔐 네이버 세션 생성기",
            font=("맑은 고딕", 20, "bold"),
            bg="#4F46E5",
            fg="white"
        ).pack(pady=10)
        
        tk.Label(
            header_frame,
            text="리뷰 관리 시스템",
            font=("맑은 고딕", 10),
            bg="#4F46E5",
            fg="white"
        ).pack()
        
        # 메인 컨텐츠
        main_frame = tk.Frame(self.window, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 설명
        info_text = (
            "네이버 스마트플레이스 계정 정보를 입력하세요.\n"
            "자동으로 로그인 후 세션이 생성됩니다."
        )
        tk.Label(
            main_frame,
            text=info_text,
            font=("맑은 고딕", 10),
            fg="#666",
            justify=tk.LEFT
        ).pack(pady=(0, 20))
        
        # 아이디 입력
        tk.Label(
            main_frame,
            text="네이버 아이디",
            font=("맑은 고딕", 10, "bold")
        ).pack(anchor=tk.W)
        
        self.username_entry = tk.Entry(
            main_frame,
            font=("맑은 고딕", 11),
            width=40
        )
        self.username_entry.pack(pady=(5, 15), ipady=5)
        
        # 비밀번호 입력
        tk.Label(
            main_frame,
            text="비밀번호",
            font=("맑은 고딕", 10, "bold")
        ).pack(anchor=tk.W)
        
        self.password_entry = tk.Entry(
            main_frame,
            font=("맑은 고딕", 11),
            width=40,
            show="●"
        )
        self.password_entry.pack(pady=(5, 20), ipady=5)
        
        # 주의사항
        warning_frame = tk.Frame(main_frame, bg="#FEF3C7", relief=tk.SOLID, borderwidth=1)
        warning_frame.pack(fill=tk.X, pady=(0, 20))
        
        warning_text = (
            "⚠️ 주의사항\n\n"
            "• 2단계 인증이 필요합니다\n"
            "• 브라우저가 자동으로 열립니다\n"
            "• 로그인 완료까지 대기해주세요\n"
            "• SMS 인증 또는 앱 인증을 완료해주세요"
        )
        tk.Label(
            warning_frame,
            text=warning_text,
            font=("맑은 고딕", 9),
            bg="#FEF3C7",
            fg="#92400E",
            justify=tk.LEFT
        ).pack(padx=15, pady=10)
        
        # 진행 상황
        self.progress_label = tk.Label(
            main_frame,
            text="",
            font=("맑은 고딕", 9),
            fg="#666"
        )
        self.progress_label.pack(pady=(0, 10))
        
        # 프로그레스 바
        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=(0, 20))
        
        # 버튼 프레임
        button_frame = tk.Frame(main_frame)
        button_frame.pack()
        
        # 시작 버튼
        self.start_button = tk.Button(
            button_frame,
            text="🚀 로그인 시작하기",
            font=("맑은 고딕", 12, "bold"),
            bg="#4F46E5",
            fg="white",
            activebackground="#4338CA",
            activeforeground="white",
            width=20,
            height=2,
            cursor="hand2",
            command=self.start_process
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 취소 버튼
        self.cancel_button = tk.Button(
            button_frame,
            text="❌ 취소",
            font=("맑은 고딕", 12),
            bg="#EF4444",
            fg="white",
            activebackground="#DC2626",
            activeforeground="white",
            width=10,
            height=2,
            cursor="hand2",
            command=self.cancel_process
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
    
    def update_progress(self, message, progress):
        """진행 상황 업데이트"""
        self.progress_label.config(text=message)
        self.progress_bar['value'] = progress
        self.window.update()
    
    def start_process(self):
        """로그인 프로세스 시작"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("오류", "아이디와 비밀번호를 모두 입력해주세요.")
            return
        
        if self.is_processing:
            messagebox.showwarning("알림", "이미 진행 중입니다.")
            return
        
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        
        # 별도 스레드에서 실행
        thread = threading.Thread(
            target=self.login_and_upload,
            args=(username, password)
        )
        thread.daemon = True
        thread.start()
    
    def login_and_upload(self, username, password):
        """네이버 로그인 및 세션 업로드"""
        try:
            # 1. Chrome 드라이버 준비
            self.update_progress("⏳ Chrome 브라우저 준비 중...", 10)
            
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--window-size=1200,900')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.update_progress("✅ Chrome 브라우저 준비 완료", 20)
            time.sleep(1)
            
            # 2. 네이버 로그인 페이지 열기
            self.update_progress("📄 네이버 로그인 페이지 열기...", 30)
            self.driver.get('https://nid.naver.com/nidlogin.login')
            time.sleep(2)
            
            # 3. 자동 정보 입력
            self.update_progress("⌨️ 로그인 정보 입력 중...", 40)
            
            id_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'id'))
            )
            pw_input = self.driver.find_element(By.ID, 'pw')
            
            self.driver.execute_script(f"document.getElementById('id').value = '{username}';")
            time.sleep(0.5)
            self.driver.execute_script(f"document.getElementById('pw').value = '{password}';")
            time.sleep(0.5)
            
            # 4. 로그인 버튼 클릭
            self.update_progress("🖱️ 로그인 버튼 클릭...", 50)
            login_btn = self.driver.find_element(By.CSS_SELECTOR, '.btn_login')
            login_btn.click()
            
            # 5. 2단계 인증 대기
            self.update_progress("📱 2단계 인증 대기 중... (브라우저에서 인증을 완료해주세요)", 60)
            
            # 로그인 성공 대기 (최대 2분)
            max_wait = 120
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url
                
                # 디바이스 등록 화면 처리
                if 'deviceConfirm' in current_url:
                    try:
                        buttons = [
                            ("//button[contains(., '나중에')]", "나중에"),
                            ("//button[contains(., '확인')]", "확인"),
                        ]
                        
                        for xpath, name in buttons:
                            try:
                                btn = self.driver.find_element(By.XPATH, xpath)
                                self.driver.execute_script("arguments[0].click();", btn)
                                time.sleep(2)
                                break
                            except:
                                continue
                    except:
                        pass
                    
                    time.sleep(2)
                    continue
                
                # 로그인 성공 확인
                if 'naver.com' in current_url and 'nidlogin' not in current_url and 'deviceConfirm' not in current_url:
                    break
                
                time.sleep(2)
                
                # 진행률 업데이트
                elapsed = int(time.time() - start_time)
                remaining = max_wait - elapsed
                self.update_progress(
                    f"📱 2단계 인증 대기 중... (남은 시간: {remaining}초)",
                    60 + (elapsed / max_wait * 20)
                )
            
            # 로그인 성공 확인
            current_url = self.driver.current_url
            if 'naver.com' in current_url and 'nidlogin' not in current_url and 'deviceConfirm' not in current_url:
                self.update_progress("✅ 로그인 성공!", 85)
                time.sleep(1)
                
                # 6. 쿠키 추출
                self.update_progress("💾 세션 데이터 추출 중...", 90)
                cookies = self.driver.get_cookies()
                
                # 7. 서버에 업로드
                self.update_progress(f"⬆️ 서버에 업로드 중... ({len(cookies)}개 쿠키)", 95)
                
                response = requests.post(
                    f"{self.api_url}/api/naver/session/upload",
                    json={
                        "cookies": cookies,
                        "user_id": "default",
                        "username": username
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    self.update_progress("🎉 완료!", 100)
                    
                    # 성공 다이얼로그
                    self.window.after(0, lambda: self.show_success(len(cookies)))
                else:
                    raise Exception(f"서버 업로드 실패: {response.status_code}")
            else:
                raise Exception("로그인에 실패했습니다. 다시 시도해주세요.")
        
        except Exception as e:
            error_msg = str(e)
            self.window.after(0, lambda: messagebox.showerror("오류", f"세션 생성 실패:\n\n{error_msg}"))
            self.update_progress("❌ 실패", 0)
        
        finally:
            # 드라이버 종료
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            
            self.is_processing = False
            self.window.after(0, lambda: self.start_button.config(state=tk.NORMAL))
    
    def show_success(self, cookie_count):
        """성공 메시지 표시"""
        success_window = tk.Toplevel(self.window)
        success_window.title("완료")
        success_window.geometry("400x300")
        success_window.resizable(False, False)
        
        # 성공 아이콘
        tk.Label(
            success_window,
            text="🎉",
            font=("맑은 고딕", 48)
        ).pack(pady=20)
        
        # 메시지
        tk.Label(
            success_window,
            text="네이버 세션이 생성되었습니다!",
            font=("맑은 고딕", 14, "bold")
        ).pack(pady=10)
        
        # 상세 정보
        info_text = f"서버에 업로드 완료\n쿠키 수: {cookie_count}개\n유효 기간: 약 7일"
        tk.Label(
            success_window,
            text=info_text,
            font=("맑은 고딕", 10),
            fg="#666"
        ).pack(pady=10)
        
        tk.Label(
            success_window,
            text="이제 웹 앱에서 네이버 리뷰를 관리할 수 있습니다!",
            font=("맑은 고딕", 10),
            fg="#4F46E5"
        ).pack(pady=10)
        
        # 버튼
        button_frame = tk.Frame(success_window)
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="🌐 웹 앱 열기",
            font=("맑은 고딕", 11, "bold"),
            bg="#4F46E5",
            fg="white",
            width=12,
            height=2,
            command=lambda: self.open_web_app(success_window)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="✅ 닫기",
            font=("맑은 고딕", 11),
            bg="#6B7280",
            fg="white",
            width=12,
            height=2,
            command=success_window.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def open_web_app(self, dialog=None):
        """웹 앱 열기"""
        import webbrowser
        webbrowser.open("https://review-management-system-ivory.vercel.app")
        if dialog:
            dialog.destroy()
    
    def cancel_process(self):
        """프로세스 취소"""
        if self.is_processing:
            if messagebox.askyesno("확인", "진행 중인 작업을 취소하시겠습니까?"):
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                self.is_processing = False
                self.start_button.config(state=tk.NORMAL)
                self.update_progress("", 0)
        else:
            self.window.quit()
    
    def run(self):
        """앱 실행"""
        self.window.mainloop()


if __name__ == "__main__":
    app = NaverSessionCreator()
    app.run()

