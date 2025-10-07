package com.ohgiraffers.tomatolab_imean.auth.controller;

import com.ohgiraffers.tomatolab_imean.common.dto.response.ApiResponseDTO;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
public class IndexController {

    @GetMapping("/api")
    public ResponseEntity<ApiResponseDTO<?>> root() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "API is running");
        response.put("version", "1.0.0");
        
        return ResponseEntity.ok(new ApiResponseDTO<>(true, "API 서버가 정상적으로 실행 중입니다.", response));
    }
}
