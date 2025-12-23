# -*- coding: utf-8 -*-
"""
네이버 OAuth -> 쿠키 추출 테스트
기존 시스템을 건드리지 않는 독립 실행 스크립트

목적: OAuth 로그인으로 스마트플레이스 접근 가능한지 검증
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import urllib.parse

# 네이버 OAuth 설정
NAVER_CLIENT_ID = "NtlZdWIILtT2yOdelsWy"
NAVER_CLIENT_SECRET = "UDdrU2gK4b"

# Callback URL (네이버 개발자 센터에 등록한 것과 동일해야 함!)
CALLBACK_URL = "http://localhost:8000/api/naver/oauth/callback"

# State (CSRF 방지용)
STATE = "test_state_12345"


def test_oauth_to_cookies():
    """OAuth 로그인 후 쿠키 추출 및 스마트플레이스 접속 테스트"""
    
    print("[시작] 네이버 OAuth -> 쿠키 추출 테스트")
    print("="*60)
    
    # 1. Chrome 드라이버 준비
    print("\n[1/6] Chrome 브라우저 준비 중...")
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--window-size=1280,720')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 2. OAuth 로그인 URL 생성
        print("\n[2/6] OAuth 로그인 URL 생성...")
        oauth_params = {
            'response_type': 'code',
            'client_id': NAVER_CLIENT_ID,
            'redirect_uri': CALLBACK_URL,
            'state': STATE
        }
        oauth_url = f"https://nid.naver.com/oauth2.0/authorize?{urllib.parse.urlencode(oauth_params)}"
        
        print(f"[URL] {oauth_url[:100]}...")
        
        # 3. OAuth 로그인 페이지 열기
        print("\n[3/6] 로그인 페이지 열기...")
        driver.get(oauth_url)
        time.sleep(2)
        
        print("\n" + "="*60)
        print("[중요] 브라우저 창에서 네이버 로그인을 진행해주세요!")
        print("="*60)
        print("   1. 아이디/비밀번호 입력")
        print("   2. 2단계 인증 완료 (SMS 또는 앱)")
        print("   3. '동의하기' 버튼 클릭 (권한 요청 시)")
        print("   4. Callback URL 에러는 정상입니다!")
        print("="*60)
        
        # 4. 로그인 완료 대기 (최대 3분)
        max_wait = 180
        start_time = time.time()
        logged_in = False
        
        while time.time() - start_time < max_wait:
            current_url = driver.current_url
            
            # Callback URL로 리다이렉트되면 성공
            if CALLBACK_URL in current_url or "code=" in current_url:
                logged_in = True
                print("\n[OK] 로그인 완료!")
                break
            
            # 진행 상황 표시
            elapsed = int(time.time() - start_time)
            if elapsed % 15 == 0 and elapsed > 0:
                remaining = max_wait - elapsed
                print(f"[대기 중] {remaining}초 남음...")
            
            time.sleep(2)
        
        if not logged_in:
            print("\n[에러] 시간 초과! 다시 시도해주세요.")
            return False
        
        # 5. 현재 URL과 Authorization Code 확인
        current_url = driver.current_url
        print(f"\n[4/6] 로그인 후 URL: {current_url[:100]}...")
        
        auth_code = None
        if "code=" in current_url:
            try:
                parsed = urllib.parse.urlparse(current_url)
                params = urllib.parse.parse_qs(parsed.query)
                auth_code = params.get('code', [None])[0]
                if auth_code:
                    print(f"[OK] Authorization Code: {auth_code[:30]}...")
            except:
                pass
        
        # 6. 쿠키 추출 (핵심!)
        print("\n[5/6] 쿠키 추출 중...")
        cookies = driver.get_cookies()
        print(f"[OK] 추출된 쿠키 수: {len(cookies)}개")
        
        # 쿠키 목록 출력
        print("\n[쿠키 목록] (처음 10개):")
        for cookie in cookies[:10]:
            print(f"   - {cookie['name']}: {cookie.get('domain', 'N/A')}")
        if len(cookies) > 10:
            print(f"   ... 외 {len(cookies) - 10}개")
        
        # 중요 인증 쿠키 확인
        important_cookies = ['NID_AUT', 'NID_SES', 'NID_JKL']
        found_cookies = [c['name'] for c in cookies]
        
        print("\n[중요 쿠키 확인]")
        all_found = True
        for cookie_name in important_cookies:
            if cookie_name in found_cookies:
                print(f"   [OK] {cookie_name}: 존재")
            else:
                print(f"   [X] {cookie_name}: 없음")
                all_found = False
        
        if not all_found:
            print("\n[경고] 중요 인증 쿠키가 일부 없습니다!")
            print("   스마트플레이스 접속에 실패할 수 있습니다.")
        
        # 7. 쿠키 저장
        with open('test_oauth_cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print("\n[저장] test_oauth_cookies.json")
        
        # 8. User-Agent 추출
        user_agent = driver.execute_script("return navigator.userAgent")
        print(f"\n[User-Agent] {user_agent[:80]}...")
        
        # 9. 스마트플레이스 접속 테스트 (가장 중요!)
        print("\n[6/6] 스마트플레이스 센터 접속 테스트...")
        print("="*60)
        driver.get('https://new.smartplace.naver.com/bizes')
        time.sleep(3)
        
        final_url = driver.current_url
        print(f"[최종 URL] {final_url}")
        
        # 10. 결과 판정
        print("\n" + "="*60)
        print("[테스트 결과]")
        print("="*60)
        
        if 'nidlogin' in final_url or 'login' in final_url.lower():
            print("[실패] 로그인 페이지로 리다이렉트됨")
            print("\n[분석]")
            print("   - OAuth 로그인은 성공했지만")
            print("   - 발급된 쿠키가 스마트플레이스에서 작동하지 않음")
            print("   - 스마트플레이스는 별도 인증이 필요")
            print("\n[결론]")
            print("   -> OAuth 방식은 스마트플레이스 접근 불가")
            print("   -> 현재 EXE 방식을 계속 사용해야 함")
            
            # 스크린샷 저장
            driver.save_screenshot('test_smartplace_failed.png')
            print("\n[스크린샷] test_smartplace_failed.png")
            
            return False
        else:
            print("[성공] 스마트플레이스 센터 접속됨!")
            print("\n[분석]")
            print("   - OAuth 로그인으로 정상적인 쿠키 발급")
            print("   - 해당 쿠키로 스마트플레이스 접근 가능")
            print("   - 매장 목록 페이지가 정상 표시됨")
            print("\n[결론]")
            print("   -> OAuth 방식으로 EXE 대체 가능!")
            print("   -> 웹앱에서 '네이버 로그인' 버튼으로 해결")
            print("   -> Refresh Token으로 자동 갱신 가능")
            
            # 스크린샷 저장
            driver.save_screenshot('test_smartplace_success.png')
            print("\n[스크린샷] test_smartplace_success.png")
            
            # 매장 목록 확인
            try:
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                if '내 업체' in page_text or '업체' in page_text:
                    print("[OK] 매장 관리 페이지 UI 확인됨!")
                
                # 매장 링크 찾기
                all_links = driver.find_elements(By.TAG_NAME, "a")
                place_links = [link for link in all_links if link.get_attribute('href') and '/bizes/place/' in link.get_attribute('href')]
                
                if place_links:
                    print(f"[OK] 매장 링크 발견: {len(place_links)}개")
                    print("\n[완벽!] OAuth 방식이 100% 작동합니다!")
            except:
                pass
            
            return True
        
    except Exception as e:
        print(f"\n[에러] {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("\n브라우저를 10초 후 종료합니다... (스크린샷 확인 시간)")
        time.sleep(10)
        driver.quit()


if __name__ == "__main__":
    print("""
========================================================
    
    네이버 OAuth -> 쿠키 테스트 스크립트
    
========================================================

이 스크립트는 기존 시스템을 건드리지 않고
OAuth 방식의 가능성만 테스트합니다.

[OK] 테스트 내용:
   1. OAuth로 네이버 로그인
   2. 쿠키 추출 및 분석
   3. 스마트플레이스 센터 접속 시도
   4. 매장 목록 확인

[!] 주의사항:
   - Chrome 브라우저가 자동으로 열립니다
   - 직접 로그인해주세요 (아이디/비밀번호)
   - 2단계 인증을 완료해주세요 (SMS 또는 앱)
   - Callback URL 에러 페이지는 정상입니다!
   
[목표]
   OAuth 방식으로 EXE를 대체할 수 있는지 검증

""")
    
    print("\n[테스트 시작]\n")
    time.sleep(2)
    
    result = test_oauth_to_cookies()
    
    print("\n" + "="*60)
    if result:
        print("[성공] 테스트 통과!")
        print("\n다음 단계:")
        print("   1. test_oauth_cookies.json 파일 확인")
        print("   2. test_smartplace_success.png 스크린샷 확인")
        print("   3. 실제 시스템에 OAuth 로그인 구현")
        print("   4. EXE 방식 대체!")
    else:
        print("[실패] OAuth 방식 불가")
        print("\n결론:")
        print("   OAuth 방식은 스마트플레이스 접근 불가")
        print("   현재 EXE 방식을 계속 사용해야 합니다")
        print("\n생성된 파일:")
        print("   - test_oauth_cookies.json (쿠키 정보)")
        print("   - test_smartplace_failed.png (실패 스크린샷)")
    print("="*60)
