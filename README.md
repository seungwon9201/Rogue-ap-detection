데이터셋(Wireshark를 통한 데이터 수집)
SSID, BSSID, 채널, 신호 세기, 암호화 방식, 지원 속도, 비콘 간격, 예상 RTT, 벤더 OUI 



동작과정
![image](https://github.com/user-attachments/assets/e95fca50-6868-437f-8686-2a27d81841b2)
main.py 실행시 T-shark를 통한 네트워크 실시간 수집


![image](https://github.com/user-attachments/assets/4ad54666-237c-428a-9f4d-d916d5b81b59)
일정시간 수집후 csv파일 형태로 저장(저장공간 효율성을 위해 일정시간 수집된 데이터는 delete_script.py코드를 통해 자동 삭제)


![image](https://github.com/user-attachments/assets/8b152ba7-d532-4398-b1db-b0c036f746ff)
이러한 형태로 데이터 저장

![image](https://github.com/user-attachments/assets/6a8e4301-eacc-4d7c-aa1a-182a0bff376b)
서버측에서 데이터 로드 후 확인

![image](https://github.com/user-attachments/assets/fb7d4389-d86e-4bfe-93d6-4df128383798)
학습된 모델이 탐지해서 의심되는 rogue ap목록을 1.txt파일로 생성

![image](https://github.com/user-attachments/assets/cc2d8e31-9651-472f-9997-bba5e1473502)
최종 검증을 위한 RTT값 계산, 그래프 시각화
