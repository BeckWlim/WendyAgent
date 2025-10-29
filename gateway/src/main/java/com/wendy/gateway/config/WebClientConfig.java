package com.wendy.gateway.config;

import org.springframework.cloud.client.loadbalancer.LoadBalanced;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {

    @Bean
    @LoadBalanced  // ✅ 核心注解，让 WebClient 支持 lb://
    public WebClient.Builder webClientBuilder() {
        return WebClient.builder();
    }
}
