from services.auth import email_validation


def validate_campaign_name(name: str) -> str | None:
    stripped = name.strip()
    if not stripped:
        return "Campaign name is required."
    if len(stripped) > 255:
        return "Campaign name must be at most 255 characters."
    return None


def validate_email_content(content: str) -> str | None:
    if not content or not content.strip():
        return "Email content is required."
    return None


def validate_target_email(raw_email: str) -> tuple[str | None, str | None]:
    email, error = email_validation.validate_and_normalize_email(raw_email)
    if error:
        return None, error
    return email, None


def parse_target_groups(raw_groups) -> tuple[list[dict] | None, str | None]:
    if raw_groups is None:
        return [], None

    if not isinstance(raw_groups, list):
        return None, "target_groups must be an array."

    parsed: list[dict] = []
    for index, group in enumerate(raw_groups):
        if not isinstance(group, dict):
            return None, f"target_groups[{index}] must be an object."

        group_name = (group.get("name") or "").strip()
        if not group_name:
            return None, f"target_groups[{index}].name is required."
        if len(group_name) > 255:
            return None, f"target_groups[{index}].name must be at most 255 characters."

        raw_targets = group.get("targets", [])
        if raw_targets is None:
            raw_targets = []
        if not isinstance(raw_targets, list):
            return None, f"target_groups[{index}].targets must be an array."

        targets: list[dict] = []
        seen_emails: set[str] = set()
        for t_index, target in enumerate(raw_targets):
            if not isinstance(target, dict):
                return (
                    None,
                    f"target_groups[{index}].targets[{t_index}] must be an object.",
                )

            raw_email = target.get("email")
            if not isinstance(raw_email, str) or not raw_email.strip():
                return (
                    None,
                    f"target_groups[{index}].targets[{t_index}].email is required.",
                )

            email, email_error = validate_target_email(raw_email)
            if email_error:
                return (
                    None,
                    f"target_groups[{index}].targets[{t_index}].email: {email_error}",
                )
            if email in seen_emails:
                return (
                    None,
                    f"Duplicate email in group '{group_name}': {email}",
                )
            seen_emails.add(email)

            target_name = target.get("name")
            if target_name is not None:
                if not isinstance(target_name, str):
                    return (
                        None,
                        f"target_groups[{index}].targets[{t_index}].name must be a string.",
                    )
                target_name = target_name.strip() or None
                if target_name and len(target_name) > 255:
                    return (
                        None,
                        f"target_groups[{index}].targets[{t_index}].name must be at most 255 characters.",
                    )

            targets.append({"email": email, "name": target_name})

        parsed.append({"name": group_name, "targets": targets})

    return parsed, None
