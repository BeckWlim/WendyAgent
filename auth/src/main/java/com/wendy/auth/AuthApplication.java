package com.wendy.auth;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.data.redis.repository.configuration.EnableRedisRepositories;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

// 主启动注解：开启 Spring Boot 自动配置、组件扫描等
@SpringBootApplication
// 启用 JPA 仓库（若使用 JpaRepository）
@EnableJpaRepositories(basePackages = "com.wendy.auth.repository")
// 启用 Redis 仓库（若使用 Redis 相关 Repository）
@EnableRedisRepositories(basePackages = "com.wendy.auth.repository")
@EnableDiscoveryClient
public class AuthApplication {

    // 程序入口：启动 Spring Boot 应用
    public static void main(String[] args) {
        SpringApplication.run(AuthApplication.class, args);
    }
}
