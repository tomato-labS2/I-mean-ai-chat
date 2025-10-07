package com.ohgiraffers.tomatolab_imean.members.model.common;

public enum MemberRole {
    MEMBER("회원"),
    GENERAL_ADMIN("매니저"),
    SUPER_ADMIN("관리자");

    private final String description;

    MemberRole(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}
