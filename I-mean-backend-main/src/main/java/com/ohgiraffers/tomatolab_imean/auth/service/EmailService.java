package com.ohgiraffers.tomatolab_imean.auth.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

import java.util.Random;

/**
 * 이메일 전송 서비스
 * 회원가입 인증, 비밀번호 재설정 등에 사용
 */
@Service
public class EmailService {
    
    private final JavaMailSender javaMailSender;
    
    @Value("${spring.mail.username:noreply@imean.com}")
    private String fromEmail;
    
    @Autowired
    public EmailService(JavaMailSender javaMailSender) {
        this.javaMailSender = javaMailSender;
    }
    
    /**
     * 인증 코드 생성
     * 6자리 숫자로 구성
     */
    public String generateVerificationCode() {
        Random random = new Random();
        int code = 100000 + random.nextInt(900000);
        return String.valueOf(code);
    }
    
    /**
     * 회원가입 인증 이메일 발송
     */
    public void sendVerificationEmail(String to, String verificationCode) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(fromEmail);
        message.setTo(to);
        message.setSubject("[I-MEAN] 회원가입 인증번호");
        message.setText(
            "안녕하세요!\n\n" +
            "I-MEAN 회원가입을 위한 인증번호입니다.\n\n" +
            "인증번호: " + verificationCode + "\n\n" +
            "이 인증번호는 5분간 유효합니다.\n\n" +
            "감사합니다.\n" +
            "I-MEAN 팀"
        );
        
        javaMailSender.send(message);
    }
    
    /**
     * 비밀번호 재설정 이메일 발송
     */
    public void sendPasswordResetEmail(String to, String resetToken) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(fromEmail);
        message.setTo(to);
        message.setSubject("[I-MEAN] 비밀번호 재설정");
        message.setText(
            "안녕하세요!\n\n" +
            "비밀번호 재설정을 요청하셨습니다.\n\n" +
            "재설정 코드: " + resetToken + "\n\n" +
            "이 코드는 10분간 유효합니다.\n\n" +
            "만약 비밀번호 재설정을 요청하지 않으셨다면 이 메일을 무시해주세요.\n\n" +
            "감사합니다.\n" +
            "I-MEAN 팀"
        );
        
        javaMailSender.send(message);
    }
    
    /**
     * 일반 이메일 발송
     */
    public void sendEmail(String to, String subject, String content) {
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(fromEmail);
        message.setTo(to);
        message.setSubject(subject);
        message.setText(content);
        
        javaMailSender.send(message);
    }
}
