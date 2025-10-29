package com.wendy.common.config;

import org.springframework.amqp.core.Queue;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    @Bean
    public Queue requestQueue() {
        return new Queue("agent.request.queue", true); // durable
    }

    @Bean
    public Queue responseQueue() {
        return new Queue("agent.response.queue", true); // durable
    }
}
