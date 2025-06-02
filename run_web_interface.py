#!/usr/bin/env python3
"""
WPAA Web Interface Runner
"""

import sys
import os
import logging

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from web_interface import WebInterface
    
    def main():
        print("=" * 60)
        print("WPAA - Web Page Architecture Analyzer Interface")
        print("=" * 60)
        print()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Start web interface
        web_interface = WebInterface()
        
        print("🌐 웹 서버를 시작합니다...")
        print("📱 브라우저에서 다음 주소로 접속하세요:")
        print("   http://127.0.0.1:5000")
        print()
        print("💡 팁:")
        print("   - Ctrl+C로 서버를 종료할 수 있습니다.")
        print("   - 웹 인터페이스에서 URL을 입력하여 분석을 시작하세요.")
        print("   - 변경사항 비교 기능을 사용해 사이트 업데이트를 추적하세요.")
        print()
        
        try:
            web_interface.run(host='127.0.0.1', port=5000, debug=False)
        except KeyboardInterrupt:
            print("\n\n서버가 종료되었습니다.")
        except Exception as e:
            print(f"\n오류가 발생했습니다: {e}")
            print("requirements.txt의 패키지들이 모두 설치되었는지 확인해주세요.")
            print("pip install -r requirements.txt")

except ImportError as e:
    print("필수 모듈을 가져올 수 없습니다.")
    print(f"오류: {e}")
    print()
    print("다음 명령어로 필수 패키지를 설치해주세요:")
    print("pip install -r requirements.txt")
    sys.exit(1)

if __name__ == "__main__":
    main()