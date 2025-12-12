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
        self.window.geometry("520x650")  # 버튼이 보이도록
        self.window.resizable(True, True)
        
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
        main_frame = tk.Frame(self.window, padx=25, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 설명
        info_text = (
            "Google 계정과 연결하여 네이버 세션을 생성합니다.\n"
            "자동으로 로그인 후 세션이 저장됩니다."
        )
        tk.Label(
            main_frame,
            text=info_text,
            font=("맑은 고딕", 10),
            fg="#666",
            justify=tk.LEFT
        ).pack(pady=(0, 10))
        
        # 🚀 Google Email 입력 (여러 개 가능)
        tk.Label(
            main_frame,
            text="Google Email (필수)",
            font=("맑은 고딕", 10, "bold")
        ).pack(anchor=tk.W)
        
        google_email_frame = tk.Frame(main_frame)
        google_email_frame.pack(anchor=tk.W, pady=(5, 5), fill=tk.X)
        
        # 여러 줄 입력 가능한 Text 위젯
        self.google_email_text = tk.Text(
            google_email_frame,
            font=("맑은 고딕", 9),
            width=42,
            height=2,  # 2줄로 축소
            wrap=tk.WORD
        )
        self.google_email_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            main_frame,
            text="💡 여러 계정: user1@gmail.com, user2@gmail.com",
            font=("맑은 고딕", 7),
            fg="#999"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # 네이버 아이디 입력
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
        
        # 주의사항 (축소)
        tk.Label(
            main_frame,
            text="⚠️ 2단계 인증 필요 | 브라우저 자동 열림 | SMS/앱 인증 완료",
            font=("맑은 고딕", 8),
            fg="#92400E",
            bg="#FEF3C7",
            relief=tk.SOLID,
            borderwidth=1
        ).pack(fill=tk.X, pady=(0, 10), padx=2, ipady=8)
        
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
        self.progress_bar.pack(pady=(0, 15))
        
        # 🚀 다른 Google 계정 추가 옵션
        self.add_another_var = tk.BooleanVar(value=False)
        add_another_check = tk.Checkbutton(
            main_frame,
            text="✅ 완료 후 다른 Google 계정 추가 (같은 네이버 세션에)",
            variable=self.add_another_var,
            font=("맑은 고딕", 9),
            fg="#4F46E5"
        )
        add_another_check.pack(pady=(0, 10))
        
        # 버튼 프레임
        button_frame = tk.Frame(main_frame)
        button_frame.pack()
        
        # 시작 버튼
        self.start_button = tk.Button(
            button_frame,
            text="🚀 로그인 시작하기",
            font=("맑은 고딕", 14, "bold"),
            bg="#4F46E5",
            fg="white",
            activebackground="#4338CA",
            activeforeground="white",
            width=18,
            height=2,
            cursor="hand2",
            relief=tk.RAISED,
            bd=3,
            command=self.start_process
        )
        self.start_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        # 취소 버튼
        self.cancel_button = tk.Button(
            button_frame,
            text="✖ 취소",
            font=("맑은 고딕", 14, "bold"),
            bg="#EF4444",
            fg="white",
            activebackground="#DC2626",
            activeforeground="white",
            width=12,
            height=2,
            cursor="hand2",
            relief=tk.RAISED,
            bd=3,
            command=self.cancel_process
        )
        self.cancel_button.pack(side=tk.LEFT, padx=10, pady=10)
    
    def update_progress(self, message, progress):
        """진행 상황 업데이트"""
        self.progress_label.config(text=message)
        self.progress_bar['value'] = progress
        self.window.update()
    
    def start_process(self):
        """로그인 프로세스 시작"""
        # 🚀 여러 개의 Google Email 파싱
        google_emails_input = self.google_email_text.get("1.0", tk.END).strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Google Email 검증 및 파싱
        if not google_emails_input:
            messagebox.showerror("오류", "Google Email을 입력해주세요.")
            return
        
        # 쉼표, 공백, 줄바꿈으로 분리
        import re
        google_emails = re.split(r'[,\n\s]+', google_emails_input)
        google_emails = [email.strip() for email in google_emails if email.strip()]
        
        # 이메일 형식 검증
        for email in google_emails:
            if "@" not in email or "." not in email:
                messagebox.showerror("오류", f"올바른 이메일 형식이 아닙니다:\n{email}\n\n예: user@gmail.com")
                return
        
        # 쉼표로 연결하여 전달
        google_email = ",".join(google_emails)
        
        if not username or not password:
            messagebox.showerror("오류", "네이버 아이디와 비밀번호를 모두 입력해주세요.")
            return
        
        if self.is_processing:
            messagebox.showwarning("알림", "이미 진행 중입니다.")
            return
        
        self.is_processing = True
        self.start_button.config(state=tk.DISABLED)
        
        # 네이버 아이디를 계정 ID로 사용
        account_id = username
        
        # 별도 스레드에서 실행
        thread = threading.Thread(
            target=self.login_and_upload,
            args=(account_id, username, password, google_email)  # google_email 추가
        )
        thread.daemon = True
        thread.start()
    
    def login_and_upload(self, account_id, username, password, google_email):
        """네이버 로그인 및 세션 업로드"""
        try:
            print(f"🔗 Connecting session to Google account: {google_email}")
            # 0. Heroku 서버 깨우기 (Cold Start 방지)
            self.update_progress("🔌 서버 연결 확인 중...", 5)
            try:
                print("🔌 Warming up Heroku server...")
                ping_response = requests.get(f"{self.api_url}/health", timeout=60)
                print(f"✅ Server is awake: {ping_response.status_code}")
            except Exception as e:
                print(f"⚠️ Server ping warning: {e}")
                # Continue anyway
            
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
                
                # 7. 서버에 업로드 (재시도 로직 포함)
                self.update_progress(f"⬆️ 서버에 업로드 중... ({len(cookies)}개 쿠키)", 95)
                
                max_retries = 3
                upload_success = False
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        if attempt > 0:
                            print(f"🔄 업로드 재시도 {attempt + 1}/{max_retries}...")
                            self.update_progress(f"🔄 재시도 중... ({attempt + 1}/{max_retries})", 95)
                            time.sleep(2)  # Wait before retry
                        
                        # 🚀 Google email을 쿼리 파라미터로 전달
                        upload_url = f"{self.api_url}/api/naver/session/upload?google_email={google_email}"
                        
                        response = requests.post(
                            upload_url,
                            json={
                                "cookies": cookies,
                                "user_id": account_id,
                                "username": username
                            },
                            timeout=90
                        )
                        
                        if response.status_code == 200:
                            upload_success = True
                            break
                        else:
                            last_error = f"HTTP {response.status_code}: {response.text[:100]}"
                            
                    except requests.exceptions.Timeout:
                        last_error = "서버 응답 시간 초과 (90초)"
                        print(f"⏰ Timeout on attempt {attempt + 1}")
                    except Exception as e:
                        last_error = str(e)
                        print(f"❌ Upload error on attempt {attempt + 1}: {e}")
                
                if upload_success:
                    self.update_progress("🎉 완료!", 100)
                    
                    # 🚀 다른 계정 추가 옵션 확인
                    add_another = self.add_another_var.get()
                    
                    # 성공 다이얼로그
                    self.window.after(0, lambda: self.show_success(len(cookies), add_another, google_email))
                else:
                    raise Exception(f"서버 업로드 실패 ({max_retries}회 시도): {last_error}")
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
    
    def show_success(self, cookie_count, add_another=False, google_email=""):
        """성공 메시지 표시"""
        success_window = tk.Toplevel(self.window)
        success_window.title("완료")
        success_window.geometry("450x400")  # 버튼이 보이도록
        success_window.resizable(True, True)
        
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
        
        # 🚀 다른 계정 추가 버튼 (옵션 선택 시)
        if add_another:
            tk.Button(
                button_frame,
                text="➕ 다른 계정 추가",
                font=("맑은 고딕", 11, "bold"),
                bg="#10B981",
                fg="white",
                width=15,
                height=2,
                command=lambda: self.add_another_account(success_window, google_email)
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
    
    def add_another_account(self, success_window, google_email):
        """다른 Google 계정 추가 (같은 네이버 세션에)"""
        success_window.destroy()
        
        # Google Email 초기화 (새로운 계정 입력)
        self.google_email_text.delete("1.0", tk.END)
        
        # 네이버 정보는 유지
        # 진행률 초기화
        self.update_progress("대기 중...", 0)
        
        messagebox.showinfo(
            "다른 Google 계정 추가",
            "같은 네이버 세션에 다른 Google 계정을 추가합니다.\n\n새로운 Google Email을 입력하고 로그인하세요."
        )
    
    def run(self):
        """앱 실행"""
        self.window.mainloop()


if __name__ == "__main__":
    app = NaverSessionCreator()
    app.run()

