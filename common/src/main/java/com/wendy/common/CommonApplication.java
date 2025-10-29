package com.wendy.common;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.data.redis.repository.configuration.EnableRedisRepositories;

@SpringBootApplication
@EnableDiscoveryClient
@EnableRedisRepositories(basePackages = "com.wendy.common.repository")
public class CommonApplication {
    public static void main(String[] args){
        SpringApplication.run(CommonApplication.class, args);
    }
}
