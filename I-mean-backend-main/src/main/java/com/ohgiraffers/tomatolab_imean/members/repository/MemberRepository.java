package com.ohgiraffers.tomatolab_imean.members.repository;


import com.ohgiraffers.tomatolab_imean.members.model.entity.Members;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface MemberRepository extends CrudRepository<Members, Long> {

    boolean existsByMemberCode(String memberCode);

    boolean existsByMemberEmail(String memberEmail);

    boolean existsByMemberPhone(String memberPhone);

    Optional<Members> findByMemberEmail(String email);

    Optional<Members> findByMemberCode(String code);
}