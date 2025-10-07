package com.ohgiraffers.tomatolab_imean.auth.exception;

import org.springframework.security.core.AuthenticationException;

public class UserStatusException extends AuthenticationException {
    
    public UserStatusException(String msg) {
        super(msg);
    }
    
    public UserStatusException(String msg, Throwable cause) {
        super(msg, cause);
    }
}