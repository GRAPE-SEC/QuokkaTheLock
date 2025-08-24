// keygen.go
package main

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"fmt"
	"log"
	"os"
)

// savePEMKey 는 RSA 개인키를 PEM 형식의 파일로 저장합니다.
func savePEMKey(fileName string, key *rsa.PrivateKey) {
	outFile, err := os.Create(fileName)
	if err != nil {
		log.Fatalf("파일 생성 실패: %v", err)
	}
	defer outFile.Close()

	privateKeyBytes := x509.MarshalPKCS1PrivateKey(key)
	if err := pem.Encode(outFile, &pem.Block{Type: "RSA PRIVATE KEY", Bytes: privateKeyBytes}); err != nil {
		log.Fatalf("키 저장 실패: %v", err)
	}
}

// savePublicPEMKey 는 RSA 공개키를 PEM 형식의 파일로 저장합니다.
func savePublicPEMKey(fileName string, pubkey *rsa.PublicKey) {
	pubKeyBytes := x509.MarshalPKCS1PublicKey(pubkey)
	outFile, err := os.Create(fileName)
	if err != nil {
		log.Fatalf("파일 생성 실패: %v", err)
	}
	defer outFile.Close()
	if err := pem.Encode(outFile, &pem.Block{Type: "RSA PUBLIC KEY", Bytes: pubKeyBytes}); err != nil {
		log.Fatalf("공개키 저장 실패: %v", err)
	}
}

func main() {
	fmt.Println("2048비트 RSA 키 쌍을 생성합니다...")
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		log.Fatalf("RSA 키 생성 실패: %v", err)
	}

	// 파일로 저장
	savePEMKey("private.pem", privateKey)
	savePublicPEMKey("public.pem", &privateKey.PublicKey)

	fmt.Println("'private.pem'과 'public.pem' 파일이 생성되었습니다.")
	fmt.Println("\n--- 다음 공개키 내용을 복사하여 go_lock 프로그램에 붙여넣으세요 ---")

	// 화면에 public.pem 내용 출력
	pubKeyBytes, _ := os.ReadFile("public.pem")
	fmt.Println(string(pubKeyBytes))
}
