import os
import time
import sys

def delete_file(file_path, delay_seconds):
    """ Delete the file after a certain delay in seconds. """
    print(f"File {file_path} will be deleted in {delay_seconds} seconds.")
    time.sleep(delay_seconds)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            # 삭제 후 메시지 출력 없음
        except OSError as e:
            # 오류가 발생하면 메시지를 출력하지만, 이 예제에서는 출력하지 않도록 설정됨
            pass
    else:
        # 파일이 이미 삭제된 경우 메시지를 출력하지 않음
        pass

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 delete_script.py <file_path> <delay_seconds>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    delay_seconds = int(sys.argv[2])
    
    delete_file(file_path, delay_seconds)

