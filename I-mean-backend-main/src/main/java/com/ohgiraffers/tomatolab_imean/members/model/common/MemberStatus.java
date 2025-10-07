package com.ohgiraffers.tomatolab_imean.members.model.common;

public enum MemberStatus {
    ACTIVE("활성"),    DORMANT("휴면"),
    BLOCKED("차단"),    DELETED("삭제");


    private final String description;

    MemberStatus(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }
}



