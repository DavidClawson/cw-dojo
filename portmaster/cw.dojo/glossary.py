"""CW glossary — common abbreviations, prosigns, and phrases.

Each term has: abbreviation, meaning, history/origin, category.
VOCAB_ORDER defines the learning sequence for the vocab trainer.
"""

# Categories of common CW terms — (abbrev, meaning) for glossary browser
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


# --- Vocabulary trainer data ---
# (abbrev, meaning, history) ordered from most essential to least.
# This is the learning sequence for the vocab trainer.

VOCAB_ORDER = [
    # --- Essentials: you need these for any QSO ---
    ('CQ', 'Calling any station',
     'Possibly from French "securite" or "seek you." '
     'Used since early 1900s maritime radio to call any listening station.'),

    ('DE', 'From (this is...)',
     'French for "from." International telegraphers adopted French terms '
     'since the early telegraph conventions were held in Paris.'),

    ('K', 'Go ahead, over to you',
     'Short for "key" — go ahead and key your transmitter. '
     'One of the oldest procedural signals in radiotelegraphy.'),

    ('R', 'Roger / Received',
     'Short for "received." In voice radio this became "Roger" '
     'from the old phonetic alphabet where R = Roger.'),

    ('73', 'Best regards',
     'From the Phillips Code of 1859, used by landline telegraphers. '
     'Originally meant "my compliments" — evolved to "best regards" over time.'),

    ('TNX', 'Thanks',
     'Shorthand for "thanks." CW operators shorten common words '
     'to save time — every character counts at 20 WPM.'),

    # --- Signal reports & Q-codes ---
    ('RST', 'Readability-Strength-Tone',
     'Standardized signal reporting: R (1-5 readability), '
     'S (1-9 strength), T (1-9 tone quality). Created for CW.'),

    ('599', 'Perfect signal report',
     'RST 599 = perfectly readable, very strong, pure tone. '
     'In contests, 599 is given almost universally regardless of actual signal.'),

    ('QTH', 'My location is...',
     'From the Q-code system created by the British government in 1909 '
     'for international maritime radio. "Q" codes let operators who '
     "didn't share a language still communicate."),

    ('QSL', 'I confirm / I acknowledge',
     'Q-code for confirmation. QSL cards — postcards confirming a contact — '
     'became a beloved ham radio tradition and are still exchanged today.'),

    ('QSO', 'A radio contact / conversation',
     'Q-code meaning a two-way communication. Hams say '
     '"I had a nice QSO" meaning a good conversation on the air.'),

    ('QRZ?', 'Who is calling me?',
     'Q-code query: "who is calling?" Often heard when a station '
     "can't quite copy the caller's sign. QRZ.com is named after this."),

    # --- Prosigns ---
    ('SK', 'End of contact',
     'Sent as a single character (not S then K). Means "end of contact." '
     'Also used as a tribute when a ham passes away — "silent key."'),

    ('AR', 'End of message',
     'Sent as a single prosign. Means "end of this message" but '
     'not end of the contact. You may still continue talking.'),

    ('BK', 'Break',
     'Invitation to transmit. Used in casual QSOs instead of K, '
     'meaning "go ahead, break in anytime" — more conversational.'),

    ('KN', 'Go ahead, named station only',
     'Like K but exclusive — only the named station should respond. '
     'Used when you want to prevent others from breaking in.'),

    # --- Conversation builders ---
    ('FER', 'For',
     'Shorthand for "for." Combined with TNX: "TNX FER CALL" = '
     '"thanks for the call" — one of the most common CW phrases.'),

    ('UR', 'Your / You are',
     'Shorthand for "your" or "you are." "UR RST 599" = '
     '"your signal report is 599."'),

    ('ES', 'And',
     'Shorthand for "and." From early telegraph shorthand. '
     '"73 ES TNX FER QSO" = "best regards and thanks for the contact."'),

    ('HR', 'Here / Hear',
     'Shorthand for "here" or "hear." '
     '"NAME HR BOB" = "my name here is Bob."'),

    ('OM', 'Old man (fellow ham)',
     'Affectionate term for a male ham operator, regardless of age. '
     'From early 1900s radio culture. Not considered rude!'),

    ('FB', 'Fine business (great!)',
     'Old telegraph slang meaning "great" or "excellent." '
     '"FB OM" = "that\'s great, friend." Still widely used on CW.'),

    ('88', 'Love and kisses',
     'From the Phillips Code like 73. '
     'Less common than 73 but sometimes used between close friends or couples.'),

    ('HI', 'Laughter',
     'CW equivalent of "haha." Sent as the letters H-I. '
     'Often sent multiple times: "HI HI" = laughing.'),

    # --- More Q-codes ---
    ('QRM', 'Man-made interference',
     'Q-code for interference from other stations or electronics. '
     '"QRM" as a statement means "I am being interfered with."'),

    ('QRN', 'Natural noise / static',
     'Q-code for atmospheric noise — thunderstorms, static crashes. '
     'Distinct from QRM which is man-made.'),

    ('QSB', 'Signal fading',
     'Q-code for fading signals. HF signals bounce off the ionosphere '
     'and fade in and out — a natural part of shortwave propagation.'),

    ('QRP', 'Low power operation',
     'Q-code meaning low power. QRP operators typically use 5 watts or less. '
     'A popular challenge — how far can you reach with minimal power?'),

    # --- Less common but useful ---
    ('WX', 'Weather',
     'Shorthand for "weather." Weather is a classic QSO topic: '
     '"WX HR SUNNY ES WARM."'),

    ('CUL', 'See you later',
     'Phonetic shorthand — "C-U-L" sounds like "see you later." '
     'A friendly way to end a contact.'),

    ('GM', 'Good morning',
     'Simple greeting shorthand. Also GE (good evening) '
     'and GA (good afternoon).'),

    ('GE', 'Good evening',
     'Greeting shorthand used to open a QSO. '
     'Which one you use depends on the time of day.'),

    ('GA', 'Good afternoon / Go ahead',
     'Can mean either "good afternoon" or "go ahead" depending on context. '
     'Usually clear from the situation.'),

    ('YL', 'Young lady',
     'Female ham operator, any age. Like OM, it\'s a term of respect '
     'from early radio culture, not a comment on age.'),

    ('XYL', 'Wife',
     'Ex-young-lady — humorous ham radio term for a wife. '
     'One of the quirkier bits of CW tradition.'),
]

# Quick lookup by abbreviation
VOCAB_DICT = {abbrev: (meaning, history) for abbrev, meaning, history in VOCAB_ORDER}
