"""Global FAQ applicable to all Airbnb properties."""

GLOBAL_FAQ = {
    "check_in_time": {
        "keywords": ["check in", "check-in", "checkin", "arrive", "arrival", "get in"],
        "answer": "Standard check-in time is 3:00 PM. Early check-in may be available upon request, subject to availability.",
    },
    "check_out_time": {
        "keywords": ["check out", "check-out", "checkout", "leave", "departure", "leaving"],
        "answer": "Standard check-out time is 11:00 AM. Late check-out may be available upon request, subject to availability.",
    },
    "smoking": {
        "keywords": ["smok", "cigarette", "vape", "vaping"],
        "answer": "All our properties are strictly non-smoking indoors. Smoking is only permitted in designated outdoor areas.",
    },
    "pets": {
        "keywords": ["pet", "dog", "cat", "animal"],
        "answer": "Our pet policy varies by property. Please check your specific listing for pet rules.",
    },
    "parking": {
        "keywords": ["park", "car", "vehicle", "garage", "spot"],
        "answer": "Parking availability and instructions are specific to each property. Please refer to the apartment information provided at check-in.",
    },
    "wifi": {
        "keywords": ["wifi", "wi-fi", "internet", "password", "network", "connection"],
        "answer": "WiFi details are provided in your apartment welcome guide. If you have trouble connecting, please let us know.",
    },
    "guests": {
        "keywords": ["guest", "visitor", "extra person", "additional person"],
        "answer": "The number of permitted guests is stated in your booking. Please do not exceed the maximum occupancy listed.",
    },
    "noise": {
        "keywords": ["noise", "quiet", "party", "music", "loud"],
        "answer": "Please observe quiet hours between 10:00 PM and 8:00 AM out of respect for neighbors.",
    },
    "garbage": {
        "keywords": ["garbage", "trash", "waste", "recycling", "bin", "rubbish"],
        "answer": "Garbage and recycling instructions are posted in the apartment. Please follow local waste disposal guidelines.",
    },
    "emergency": {
        "keywords": ["emergency", "urgent", "fire", "flood", "danger", "ambulance", "police"],
        "answer": "For life-threatening emergencies, call 911 immediately. For property emergencies, please contact the host right away.",
    },
}

COMPLAINT_KEYWORDS = [
    "broken", "not working", "doesn't work", "won't work", "issue", "problem",
    "complaint", "complain", "unhappy", "disappointed", "terrible", "awful",
    "dirty", "unclean", "stain", "damaged", "damage", "leak", "leaking",
    "bug", "insect", "roach", "mouse", "mice", "rat", "mold", "smell",
    "noise complaint", "disturbing", "unsafe", "dangerous", "broken",
    "no hot water", "no heat", "no ac", "no air conditioning", "broken",
    "not clean", "filthy", "disgusting", "unacceptable", "refund",
]
