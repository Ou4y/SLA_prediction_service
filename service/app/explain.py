def explain_risk(ticket):
    reasons = []

    if ticket.support_level == "L4_NETWORK_VENDOR":
        reasons.append("Depends on network or external vendor")

    if ticket.priority == "High":
        reasons.append("High urgency ticket")

    if ticket.created_day == "Weekend":
        reasons.append("Reduced weekend staffing")

    return reasons