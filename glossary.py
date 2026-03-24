"""CW glossary — common abbreviations, prosigns, and phrases."""

# Categories of common CW terms
GLOSSARY = {
    'Prosigns': [
        ('AR', 'End of message'),
        ('AS', 'Wait'),
        ('BK', 'Break (invite to transmit)'),
        ('BT', 'Separator (new paragraph)'),
        ('CL', 'Closing station'),
        ('CT', 'Start copying'),
        ('KN', 'Go ahead, named station only'),
        ('SK', 'End of contact'),
        ('SN', 'Understood'),
    ],
    'Common Abbreviations': [
        ('CQ', 'Calling any station'),
        ('DE', 'From (this is...)'),
        ('K', 'Go ahead'),
        ('R', 'Roger / Received'),
        ('73', 'Best regards'),
        ('88', 'Love and kisses'),
        ('OM', 'Old man (fellow ham)'),
        ('YL', 'Young lady'),
        ('XYL', 'Wife'),
        ('HI', 'Laughter'),
    ],
    'Signal Reports': [
        ('RST', 'Readability-Strength-Tone'),
        ('599', 'Perfect signal'),
        ('579', 'Good signal, fair tone'),
        ('339', 'Weak but readable'),
        ('QRZ?', 'Who is calling me?'),
        ('QTH', 'My location is...'),
        ('QSL', 'I confirm / I acknowledge'),
        ('QSO', 'A contact/conversation'),
        ('QRM', 'Man-made interference'),
        ('QRN', 'Natural noise/static'),
        ('QSB', 'Signal fading'),
        ('QRP', 'Low power'),
        ('QRO', 'High power'),
    ],
    'Conversation': [
        ('TNX', 'Thanks'),
        ('FER', 'For'),
        ('UR', 'Your / You are'),
        ('HR', 'Here / Hear'),
        ('ES', 'And'),
        ('WX', 'Weather'),
        ('ANT', 'Antenna'),
        ('RIG', 'Radio equipment'),
        ('PWR', 'Power'),
        ('FB', 'Fine business (great!)'),
        ('CUL', 'See you later'),
        ('GE', 'Good evening'),
        ('GM', 'Good morning'),
        ('GA', 'Good afternoon / Go ahead'),
    ],
    'Typical QSO Flow': [
        ('CQ CQ CQ DE W1ABC K', 'Calling CQ'),
        ('W1ABC DE K2DEF K', 'Answering a CQ'),
        ('R TNX FER CALL', 'Thanks for calling'),
        ('UR RST 599 599', 'Your signal report'),
        ('NAME HR BOB', 'My name is Bob'),
        ('QTH CA', 'Location is California'),
        ('73 ES TNX FER QSO', 'Best regards, thanks'),
        ('TU DE W1ABC SK', 'Thank you, signing off'),
    ],
}

# Flat list of all terms for quick lookup
ALL_TERMS = []
for category, terms in GLOSSARY.items():
    for abbrev, meaning in terms:
        ALL_TERMS.append((abbrev, meaning, category))
