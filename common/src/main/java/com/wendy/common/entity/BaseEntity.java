package com.wendy.common.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 基础实体类（所有业务实体继承此类）
 */
@Data
public class BaseEntity {

    /**
     * 主键 ID（PostgreSQL 常用 SERIAL/BIGSERIAL 自增类型，对应 MyBatis-Plus 的 AUTO 策略）
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 创建时间（自动填充）
     */
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;

    /**
     * 更新时间（自动填充）
     */
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;

    /**
     * 逻辑删除标识（0-未删除，1-已删除）
     */
    @TableLogic
    private Integer deleted;
}