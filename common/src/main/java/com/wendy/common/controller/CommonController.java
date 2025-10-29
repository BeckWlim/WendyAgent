package com.wendy.common.controller;

import org.slf4j.LoggerFactory;
import org.slf4j.Logger;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/common")
public class CommonController {
    private static final Logger logger = LoggerFactory.getLogger(CommonController.class);

    @PostMapping("/test")
    public ResponseEntity<String> test(
        @RequestHeader("Authorization") String token,
        @RequestParam("username") String username){
        logger.debug("user: {}, token: {}", token, username);
        return ResponseEntity.ok("Test success");
    }
}
