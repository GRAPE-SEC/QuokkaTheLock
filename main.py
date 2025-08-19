"""
수박게임 알람 파일 암호화 프로그램
파일을 암호화하고 알람창을 띄우는  버전
"""
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox
import webbrowser
from pathlib import Path

from encryptor import FileEncryptor

class SimpleEncryptor:
    def __init__(self):
        self.encryptor = FileEncryptor()
        self.base_dir = Path.cwd()
        self.setup_directories()
    
    def setup_directories(self):
        """필요한 디렉토리 생성"""
        directories = ['files/to_encrypt', 'files/encrypted', 'files/backup']
        for dir_path in directories:
            (self.base_dir / dir_path).mkdir(parents=True, exist_ok=True)
        print("디렉토리 설정 완료!")
    
    def check_files_to_encrypt(self):
        """암호화할 파일들 확인"""
        to_encrypt_dir = self.base_dir / 'files' / 'to_encrypt'
        files = list(to_encrypt_dir.glob('*.txt'))  #일단 txt 파일만 찾았음
        
        if not files:
            print("암호화할 파일이 없습니다!")
            print(f"   {to_encrypt_dir} 폴더에 .txt 파일들을 넣어주세요.")
            return False
        
        print(f"발견된 파일들 ({len(files)}개):")
        for file in files:
            print(f"   {file.name}")
        return True
    
    def encrypt_files(self):
        """파일들 암호화"""
        print("\n파일 암호화 시작...")
        
        to_encrypt_dir = self.base_dir / 'files' / 'to_encrypt'
        encrypted_dir = self.base_dir / 'files' / 'encrypted'
        backup_dir = self.base_dir / 'files' / 'backup'
        
        files = list(to_encrypt_dir.glob('*.txt'))
        encrypted_files = []
        
        for file in files:
            try:
                print(f"암호화 중: {file.name}")
                
                # 백업 만들기
                backup_path = backup_dir / file.name
                backup_path.write_text(file.read_text(encoding='utf-8'), encoding='utf-8')
                
                # 파일 암호화
                content = file.read_text(encoding='utf-8')
                encrypted_content = self.encryptor.encrypt_text(content)
                
                # 암호화된 파일 저장
                encrypted_path = encrypted_dir / f"{file.stem}_encrypted.txt"
                encrypted_path.write_text(encrypted_content, encoding='utf-8')
                
                # 원본 파일 삭제
                file.unlink()
                
                encrypted_files.append(encrypted_path)
                print(f"완료: {encrypted_path.name}")
                
            except Exception as e:
                print(f"오류 ({file.name}): {e}")

        print(f"\n암호화 완료! {len(encrypted_files)}개 파일이 암호화되었습니다.")
        return len(encrypted_files) > 0
    
    def show_ransom_alert(self):
        """랜섬웨어 스타일 알람창 표시"""
        
        # tkinter 윈도우 생성
        root = tk.Tk()
        root.withdraw()  # 메인 윈도우 숨기기
        
        # 알람 메시지
        message = """ 경고! 당신의 컴퓨터는 암호화되었습니다! 

중요 파일들이 암호화되었습니다.

수박게임을 하여 수박을 성공적으로 만들면 복호화가 가능합니다.

게임 링크:
https://suika-game.app/ko
"""
        
        # 메시지박스 표시 (Yes/No 버튼)
        result = messagebox.askyesno(
            "수박게임 암호화 프로그램", 
            message + "\n\n게임을 실행하시겠습니까?",
            icon='warning'
        )
        
        if result:  # Yes 클릭 시
            try:
                # 수박게임 링크 열기
                webbrowser.open('https://suika-game.app/ko')
                print("수박게임 링크를 열었습니다!")
                
                # 추가 안내
                messagebox.showinfo(
                    "게임 안내", 
                    "수박게임을 하십시오!\n\n" +
                    "행운을 빕니다!"
                )
            except Exception as e:
                print(f"브라우저 열기 오류: {e}")
                messagebox.showerror("오류", f"브라우저를 열 수 없습니다.\n수동으로 링크를 방문해주세요:\nhttps://suika-game.app/ko")
        
        root.destroy()
    
    def decrypt_files(self):
        """파일들 복호화"""
        print("\n파일 복호화 시작...")
        
        encrypted_dir = self.base_dir / 'files' / 'encrypted'
        to_encrypt_dir = self.base_dir / 'files' / 'to_encrypt'
        
        files = list(encrypted_dir.glob('*_encrypted.txt'))
        if not files:
            print("복호화할 파일이 없습니다!")
            messagebox.showwarning("복호화 실패", "복호화할 암호화된 파일이 없습니다!")
            return False
        

        print(f"발견된 암호화 파일: {len(files)}개")
        
        decrypted_files = []
        
        for file in files:
            try:
                print(f"복호화 중: {file.name}")
                
                # 파일 복호화
                encrypted_content = file.read_text(encoding='utf-8')
                decrypted_content = self.encryptor.decrypt_text(encrypted_content)
                
                # 원본 파일명 복구
                original_name = file.name.replace('_encrypted', '')
                restored_path = to_encrypt_dir / original_name
                restored_path.write_text(decrypted_content, encoding='utf-8')
                
                # 암호화된 파일 삭제
                file.unlink()
                
                decrypted_files.append(restored_path)
                print(f"복원 완료: {original_name}")
                
            except Exception as e:
                print(f"복호화 오류 ({file.name}): {e}")
        
        print(f"\n복호화 완료! {len(decrypted_files)}개 파일이 복원되었습니다.")
        
        # 성공 메시지
        root = tk.Tk()
        root.withdraw()
        
        file_list = "\n".join([f" {f.name}" for f in decrypted_files])
        messagebox.showinfo(
            "복호화 성공!", 
            f"복호화된 파일들:\n{file_list}\n\n" +
            "파일들이 원래 위치로 복원되었습니다!"
        )
        
        root.destroy()
        return len(decrypted_files) > 0
    
    def run(self):
        """메인 실행 함수"""
        print("수박게임 알람 암호화 프로그램")
        print("="*50)
        
        while True:
            print("\n메뉴를 선택하세요:")
            print("1. 파일 암호화")
            print("2. 파일 복호화")
            print("3. 상태 확인")
            print("4. 종료")
            
            choice = input("\n선택 (1-4): ").strip()
            
            if choice == '1':
                # 암호화 실행
                if not self.check_files_to_encrypt():
                    print("\n사용법:")
                    print("files/to_encrypt/ 폴더에 .txt 파일들을 넣고 다시 시도하세요.")
                    continue
                
                if self.encrypt_files():
                    print("\n암호화 완료! 알람을 표시합니다...")
                    time.sleep(2)
                    self.show_ransom_alert()
                else:
                    print("암호화에 실패했습니다.")
            
            elif choice == '2':
                # 복호화 실행
                self.decrypt_files()
            
            elif choice == '3':
                # 상태 확인
                self.show_status()
            
            elif choice == '4':
                # 종료
                print("\n프로그램을 종료합니다.")
                break
            
            else:
                print("잘못된 선택입니다. 1-4 중에서 선택해주세요.")
    
    def show_status(self):
        """현재 상태 표시"""
        print("\n현재 상태:")
        print("-" * 30)
        
        to_encrypt_dir = self.base_dir / 'files' / 'to_encrypt'
        encrypted_dir = self.base_dir / 'files' / 'encrypted'
        backup_dir = self.base_dir / 'files' / 'backup'
        
        original_files = list(to_encrypt_dir.glob('*.txt'))
        encrypted_files = list(encrypted_dir.glob('*_encrypted.txt'))
        backup_files = list(backup_dir.glob('*.txt'))
        
        print(f"원본 파일: {len(original_files)}개")
        print(f"암호화된 파일: {len(encrypted_files)}개")
        print(f"백업 파일: {len(backup_files)}개")
        
        if encrypted_files:
            print("\n암호화된 파일 목록:")
            for file in encrypted_files:
                print(f"   {file.name}")
        
        if original_files:
            print("\n원본 파일 목록:")
            for file in original_files:
                print(f"    {file.name}")

def main():
    """메인 함수"""
    try:
        app = SimpleEncryptor()
        app.run()
    except Exception as e:
        print(f"프로그램 오류: {e}")
        input("엔터 키를 누르면 종료됩니다...")

if __name__ == "__main__":
    main()