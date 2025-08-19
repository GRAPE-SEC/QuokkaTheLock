import base64
import hashlib

class FileEncryptor:
    """파일 암호화/복호화 클래스"""
    
    def __init__(self, shift_key=13):
        self.shift_key = shift_key
        self.encoding = 'utf-8'
        self.noise_marker = "NOISE_BOUNDARY"  # 노이즈 구분자
    
    def _caesar_cipher(self, text, shift, decrypt=False):
        if decrypt:
            shift = -shift
        
        result = []
        for char in text:
            if char.isalpha():
                ascii_offset = 65 if char.isupper() else 97
                shifted = (ord(char) - ascii_offset + shift) % 26
                result.append(chr(shifted + ascii_offset))
            elif char.isdigit():
                shifted = (int(char) + shift) % 10
                result.append(str(shifted))
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _generate_deterministic_noise(self, text, length=5):
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        noise = ""
        for i in range(length):
            char_index = int(hash_hex[i % len(hash_hex)], 16) % 62
            if char_index < 26:
                noise += chr(65 + char_index)      # A-Z
            elif char_index < 52:
                noise += chr(97 + char_index - 26) # a-z
            else:
                noise += str(char_index - 52)      # 0-9
        return noise
    
    def _add_noise(self, text):
        front_noise = self._generate_deterministic_noise(text + "front", 5)
        back_noise  = self._generate_deterministic_noise(text + "back", 5)
        return f"{front_noise}{self.noise_marker}{text}{self.noise_marker}{back_noise}"
    
    def _remove_noise(self, text):
        if self.noise_marker in text:
            parts = text.split(self.noise_marker)
            if len(parts) >= 3:
                return parts[1]  # 가운데가 원본
        return text  # 노이즈가 없으면 그대로 반환
    
    def encrypt_text(self, text):
        try:
            # 1. 시저 암호
            caesar_encrypted = self._caesar_cipher(text, self.shift_key)
            
            # 2. Base64 인코딩
            encoded_bytes = caesar_encrypted.encode(self.encoding)
            base64_encoded = base64.b64encode(encoded_bytes).decode('ascii')
            
            # 3. 문자열 뒤집기
            reversed_text = base64_encoded[::-1]
            
            # 4. 마지막에 노이즈 추가
            noisy_text = self._add_noise(reversed_text)
            
            return noisy_text
        except Exception as e:
            raise Exception(f"암호화 실패: {e}")
    
    def decrypt_text(self, encrypted_text):
        try:
            # 1. 노이즈 제거
            clean_text = self._remove_noise(encrypted_text)
            
            # 2. 문자열 뒤집기 복원
            unreversed_text = clean_text[::-1]
            
            # 3. Base64 디코딩
            decoded_bytes = base64.b64decode(unreversed_text.encode('ascii'))
            decoded_text = decoded_bytes.decode(self.encoding)
            
            # 4. 시저 암호 복호화
            original_text = self._caesar_cipher(decoded_text, self.shift_key, decrypt=True)
            
            return original_text
        except Exception as e:
            raise Exception(f"복호화 실패: {e}")
    
    def encrypt_file(self, input_path, output_path):
        try:
            with open(input_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            encrypted_content = self.encrypt_text(content)
            with open(output_path, 'w', encoding=self.encoding) as f:
                f.write(encrypted_content)
            print(f"파일 암호화 완료: {input_path} -> {output_path}")
            return True
        except Exception as e:
            print(f"파일 암호화 오류: {e}")
            return False
    
    def decrypt_file(self, input_path, output_path):
        try:
            with open(input_path, 'r', encoding=self.encoding) as f:
                encrypted_content = f.read()
            decrypted_content = self.decrypt_text(encrypted_content)
            with open(output_path, 'w', encoding=self.encoding) as f:
                f.write(decrypted_content)
            print(f"파일 복호화 완료: {input_path} -> {output_path}")
            return True
        except Exception as e:
            print(f"파일 복호화 오류: {e}")
            return False
