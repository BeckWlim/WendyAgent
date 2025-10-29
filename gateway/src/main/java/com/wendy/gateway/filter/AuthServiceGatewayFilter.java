package com.wendy.gateway.filter;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;

import jakarta.validation.constraints.NotNull;
import reactor.core.publisher.Mono;

@Component
@Order(1)
public class AuthServiceGatewayFilter implements WebFilter {

    private final WebClient webClient;
    private static final Logger logger = LoggerFactory.getLogger(AuthServiceGatewayFilter.class);

    public AuthServiceGatewayFilter(WebClient.Builder webClientBuilder) {
        this.webClient = webClientBuilder.baseUrl("lb://auth-service").build();
    }

    @Override
    public @NotNull Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String path = exchange.getRequest().getPath().value();
        if (path.startsWith("/api/auth/")) {
            return chain.filter(exchange);
        }

        String token = exchange.getRequest().getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        String username = exchange.getRequest().getQueryParams().getFirst("username");
        if (token == null || token.isEmpty()) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }

        // 调用 auth-service 验证 token
        return webClient.post()
            .uri(uriBuilder -> uriBuilder
                .path("/api/auth/verify")
                .queryParam("username", username)
                .build()
            )
            .header(HttpHeaders.AUTHORIZATION, token)
            .retrieve()
            .toBodilessEntity()
            .flatMap(response -> {
                if (response.getStatusCode().is2xxSuccessful()) {
                    logger.debug("Verify success, current code: {}", exchange.getResponse().getStatusCode());
                    // 校验通过，放行
                    return chain.filter(exchange);
                } else {
                    logger.debug("Verify fail");
                    exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                    return exchange.getResponse().setComplete();
                }
            })
            .onErrorResume(e -> {
                exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                return exchange.getResponse().setComplete();
            });
    }
}