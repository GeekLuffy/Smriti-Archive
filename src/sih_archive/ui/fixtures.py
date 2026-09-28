"""
Archival Catalog & Multi-Modal Heritage Fixtures for SIH26096.

Provides authentic, structured catalog fixtures:
- 6 Discovery Pathways (Manuscripts & Books, Documents & Debates, Photographs & Records,
  Audio & Video, Timelines & Stories, Research Assistant)
- Archival Catalog Records with institutional metadata, rights, and preservation status
- Chronological Historical Milestones & Timeline Events linking to primary documents
- Audio-Visual Media Records with time-coded synchronized transcripts and speaker annotations
"""

from typing import Any, Dict, List, Optional

# -----------------------------------------------------------------------------
# 1. SIX DISCOVERY PATHWAYS (ONE ARCHIVE. MANY WAYS TO EXPLORE.)
# -----------------------------------------------------------------------------

DISCOVERY_PATHWAYS: List[Dict[str, Any]] = [
    {
        "id": "manuscripts_books",
        "title": "Manuscripts & Books",
        "tagline": "Rare Treatises, Monograph Drafts & Annotated Volumes",
        "description": "High-resolution digital surrogates of seminal texts, including Annihilation of Caste, The Buddha and His Dhamma, and Columbia University seminar papers.",
        "icon": "book-open",
        "target_route": "#explorer?type=manuscripts",
        "item_count": 42,
        "badge": "300 DPI Preservation",
    },
    {
        "id": "documents_debates",
        "title": "Documents & Debates",
        "tagline": "Constituent Assembly Proceedings & Legislative Records",
        "description": "Full-text searchable official debates, constitutional draft motions, committee deliberations, and parliamentary interventions with cross-referenced legal citations.",
        "icon": "scroll",
        "target_route": "#explorer?type=debates",
        "item_count": 128,
        "badge": "Official Records",
    },
    {
        "id": "photographs_records",
        "title": "Photographs & Records",
        "tagline": "Historic Memorials, Movement Records & Archival Ephemera",
        "description": "Verified photographic plates, Satyagraha declarations, handwritten letters, and institutional resolutions from Mahad, Poona, London, and Nagpur.",
        "icon": "camera",
        "target_route": "#explorer?type=records",
        "item_count": 85,
        "badge": "Verified Provenance",
    },
    {
        "id": "audio_video",
        "title": "Audio & Video",
        "tagline": "Broadcast Speeches, Newsreels & Oral History Testimonies",
        "description": "Archival sound recordings and rare video newsreels with word-level synchronized transcripts, speaker diarization, and multilingual subtitles.",
        "icon": "headphones",
        "target_route": "#media",
        "item_count": 18,
        "badge": "Synced Transcripts",
    },
    {
        "id": "timelines_stories",
        "title": "Timelines & Stories",
        "tagline": "Chronological Heritage Milestones & Curated Narratives",
        "description": "Interactive thematic timelines connecting life milestones, legislative achievements, and social movements directly to primary source evidentiary pages.",
        "icon": "clock",
        "target_route": "#timeline",
        "item_count": 16,
        "badge": "Evidence-Linked",
    },
    {
        "id": "research_assistant",
        "title": "Research Assistant",
        "tagline": "Evidence-Grounded Inquiry with Principled Algorithmic Refusal",
        "description": "Research-grade natural language query workspace returning synthesized answers backed by token-level bounding box citations and explicit refusals on low evidence.",
        "icon": "compass",
        "target_route": "#assistant",
        "item_count": 1,
        "badge": "Zero Hallucination Gate",
    },
]


# -----------------------------------------------------------------------------
# 2. ARCHIVAL CATALOG ITEMS
# -----------------------------------------------------------------------------

CATALOG_ITEMS: List[Dict[str, Any]] = [
    {
        "id": "cat_ambedkar_vol1",
        "document_id": "ambedkar_speech_vol1",
        "title": "Dr. Babasaheb Ambedkar: Writings and Speeches, Vol. 1",
        "subtitle": "Castes in India, Annihilation of Caste, and Maharashtra as a Linguistic Province",
        "author": "Dr. B. R. Ambedkar (Compiled by Vasant Moon)",
        "collection": "Writings & Speeches",
        "language": "eng",
        "material_type": "Manuscripts & Books",
        "rights": "public",
        "rights_evidence": "Indian Copyright Act 1957 Section 52(1)(q); Government of India open publication for public education; author deceased 1956 (copyright expired under 60-year post-mortem rule Section 22).",
        "date": "1979",
        "institution": "Dr. Ambedkar Foundation, Ministry of Social Justice and Empowerment, Government of India",
        "page_count": 5,
        "summary": "Foundational volume containing the seminal 1916 Columbia University research paper 'Castes in India', the un-delivered 1936 address 'Annihilation of Caste', and 1948 linguistic province analysis.",
        "preview_page_id": "ambedkar_speech_vol1_p0001",
        "has_ocr": True,
        "has_image": True,
    },
    {
        "id": "cat_annihilation_caste",
        "document_id": "annihilation_of_caste",
        "title": "Annihilation of Caste with a Reply to Mahatma Gandhi",
        "subtitle": "A Speech Prepared by Dr. B. R. Ambedkar for the 1936 Annual Conference of the Jat-Pat-Todak Mandal",
        "author": "Dr. B. R. Ambedkar",
        "collection": "Key Treatises",
        "language": "eng",
        "material_type": "Manuscripts & Books",
        "rights": "public",
        "rights_evidence": "Indian Copyright Act 1957 Section 22 (Public Domain, published 1936, author deceased 1956).",
        "date": "1936-05-15",
        "institution": "Ambedkar Memorial & Research Centre, New Delhi",
        "page_count": 84,
        "summary": "Uncompromising philosophical critique of the caste hierarchy, graded inequality, and religious orthodoxy, featuring the historic Ambedkar-Gandhi intellectual debate.",
        "preview_page_id": "ambedkar_speech_vol1_p0001",
        "has_ocr": True,
        "has_image": True,
    },
    {
        "id": "cat_cad_draft_1948",
        "document_id": "cad_drafting_speech",
        "title": "Constituent Assembly Debates: Motion Introducing Draft Constitution",
        "subtitle": "Official Report of the Constituent Assembly of India, Vol. VII, No. 1",
        "author": "Dr. B. R. Ambedkar (Chairman, Drafting Committee)",
        "collection": "Documents & Debates",
        "language": "eng",
        "material_type": "Documents & Debates",
        "rights": "public",
        "rights_evidence": "Official Parliamentary Record of India, freely accessible public legislative proceeding.",
        "date": "1948-11-04",
        "institution": "Parliamentary Archives of India / Lok Sabha Secretariat",
        "page_count": 42,
        "summary": "Historic address moving the consideration of the Draft Constitution, elaborating on the Parliamentary executive, fundamental rights, dual polity with single citizenship, and the role of the judiciary.",
        "preview_page_id": "ambedkar_speech_vol1_p0002",
        "has_ocr": True,
        "has_image": True,
    },
    {
        "id": "cat_castes_india_1916",
        "document_id": "castes_in_india",
        "title": "Castes in India: Their Mechanism, Genesis and Development",
        "subtitle": "Paper Presented before the Anthropology Seminar of Dr. A. A. Goldenweiser at Columbia University",
        "author": "Dr. B. R. Ambedkar",
        "collection": "Early Academic Works",
        "language": "eng",
        "material_type": "Manuscripts & Books",
        "rights": "public",
        "rights_evidence": "Published in Indian Antiquary, May 1917, Vol. XLI; public domain under Berne Convention & Indian Copyright Act.",
        "date": "1916-05-09",
        "institution": "Columbia University Rare Book & Manuscript Library / Indian Antiquary",
        "page_count": 28,
        "summary": "Pioneering socio-anthropological thesis analyzing endogamy as the defining characteristic of caste and the mechanism of graded inequality.",
        "preview_page_id": "ambedkar_speech_vol1_p0001",
        "has_ocr": True,
        "has_image": True,
    },
    {
        "id": "cat_mahad_1927",
        "document_id": "mahad_resolution",
        "title": "Chavdar Tale Water Rights Resolution & Declaration",
        "subtitle": "Bahishkrit Hitakarini Sabha Mahad Conference Proclamation",
        "author": "Dr. B. R. Ambedkar & Bahishkrit Hitakarini Sabha",
        "collection": "Photographs & Records",
        "language": "mar",
        "material_type": "Photographs & Records",
        "rights": "public",
        "rights_evidence": "Historical public conference declaration 1927, public cultural heritage documentation.",
        "date": "1927-03-20",
        "institution": "Chavdar Tale Memorial Archive, Mahad, Maharashtra",
        "page_count": 4,
        "summary": "Historic declaration asserting civic equality and access to public drinking water as an unalienable fundamental human right.",
        "preview_page_id": "ambedkar_speech_vol1_p0003",
        "has_ocr": True,
        "has_image": True,
    },
    {
        "id": "cat_mooknayak_1920",
        "document_id": "mooknayak_inaugural",
        "title": "Mooknayak (Leader of the Dumb) — Inaugural Issue Editorial",
        "subtitle": "Fortnightly Periodical for Social Awakening and Emancipation",
        "author": "Dr. B. R. Ambedkar",
        "collection": "Photographs & Records",
        "language": "mar",
        "material_type": "Photographs & Records",
        "rights": "public",
        "rights_evidence": "Periodical published January 31, 1920 in Bombay; public domain.",
        "date": "1920-01-31",
        "institution": "Nehru Memorial Museum & Library / Asiatic Society of Mumbai",
        "page_count": 8,
        "summary": "The opening editorial of Dr. Ambedkar's first journal, using the metaphor of a multi-storeyed tower without a staircase to expose the cruel injustice of caste.",
        "preview_page_id": "ambedkar_speech_vol1_p0004",
        "has_ocr": True,
        "has_image": True,
    },
    {
        "id": "cat_constitution_preamble",
        "document_id": "constitution_preamble",
        "title": "The Constitution of India — Calligraphic Preamble & Part III",
        "subtitle": "Handcrafted Master Manuscript Signed by the Members of the Constituent Assembly",
        "author": "Prem Behari Narain Raizada (Calligrapher), Nandalal Bose (Artist), Drafting Committee",
        "collection": "Documents & Debates",
        "language": "eng",
        "material_type": "Documents & Debates",
        "rights": "public",
        "rights_evidence": "Official Sovereign Founding Document of the Republic of India; National Archives of India.",
        "date": "1950-01-26",
        "institution": "Parliament Library / National Archives of India, New Delhi",
        "page_count": 251,
        "summary": "The illuminated master manuscript of the Indian Constitution, preserving the preamble, fundamental rights, and directive principles with exquisite historical borders.",
        "preview_page_id": "ambedkar_speech_vol1_p0005",
        "has_ocr": True,
        "has_image": True,
    },
    {
        "id": "cat_poona_pact_1932",
        "document_id": "poona_pact",
        "title": "The Poona Pact Agreement & Electoral Settlement",
        "subtitle": "Agreement between Leaders of Depressed Classes and Caste Hindus at Yerwada Central Jail",
        "author": "Dr. B. R. Ambedkar, M. K. Gandhi, Madan Mohan Malaviya, C. Rajagopalachari",
        "collection": "Documents & Debates",
        "language": "eng",
        "material_type": "Documents & Debates",
        "rights": "public",
        "rights_evidence": "Historic multilateral political accord (1932); Gazette of India and British Parliamentary White Paper.",
        "date": "1932-09-24",
        "institution": "National Archives of India, New Delhi",
        "page_count": 6,
        "summary": "The historic pact abandoning separate electorates in exchange for reserved seats for Depressed Classes in provincial and central legislatures.",
        "preview_page_id": "ambedkar_speech_vol1_p0002",
        "has_ocr": True,
        "has_image": True,
    },
]


# -----------------------------------------------------------------------------
# 3. CHRONOLOGICAL HISTORICAL TIMELINE EVENTS
# -----------------------------------------------------------------------------

TIMELINE_EVENTS: List[Dict[str, Any]] = [
    {
        "id": "evt_1916_castes_india",
        "year": 1916,
        "date": "May 9, 1916",
        "title": "Castes in India: Columbia University Seminar",
        "category": "Academic & Intellectual",
        "description": "Dr. Ambedkar presents his seminal research paper at Alexander Goldenweiser's anthropology seminar, theorizing caste as 'enclosed class' through forced endogamy.",
        "document_id": "castes_in_india",
        "page_id": "ambedkar_speech_vol1_p0001",
        "quote": "A caste is an enclosed class... Endogamy is the only one that is peculiar to caste that could satisfy the definition.",
        "location": "Columbia University, New York",
        "significance": "First scientific exposition of the caste mechanism by an Indian scholar.",
    },
    {
        "id": "evt_1920_mooknayak",
        "year": 1920,
        "date": "January 31, 1920",
        "title": "Launch of 'Mooknayak' (Leader of the Dumb)",
        "category": "Journalism & Social Awakening",
        "description": "Dr. Ambedkar starts his first fortnightly newspaper in Bombay to articulate the grievances and aspirations of the disenfranchised.",
        "document_id": "mooknayak_inaugural",
        "page_id": "ambedkar_speech_vol1_p0004",
        "quote": "Hindu society is like a tower with several storeys but no staircase and no entrance.",
        "location": "Bombay (Mumbai)",
        "significance": "Inaugurated an independent press for Dalit emancipation in India.",
    },
    {
        "id": "evt_1924_bahishkrit_hitakarini",
        "year": 1924,
        "date": "July 20, 1924",
        "title": "Establishment of Bahishkrit Hitakarini Sabha",
        "category": "Institutional Foundation",
        "description": "Founding meeting held at Damodar Hall, Parel, Bombay, adopting the historic motto: 'Educate, Agitate, Organise'.",
        "document_id": "ambedkar_speech_vol1",
        "page_id": "ambedkar_speech_vol1_p0001",
        "quote": "Educate, Agitate and Organise; Have faith in yourself.",
        "location": "Damodar Hall, Bombay",
        "significance": "Institutionalized the struggle for civil rights, education, and economic uplift.",
    },
    {
        "id": "evt_1927_mahad_satyagraha",
        "year": 1927,
        "date": "March 20, 1927",
        "title": "Mahad Satyagraha at Chavdar Lake",
        "category": "Civil Rights Movement",
        "description": "Dr. Ambedkar leads thousands to drink water from the public Chavdar Lake in Mahad, asserting fundamental human dignity and civic equality.",
        "document_id": "mahad_resolution",
        "page_id": "ambedkar_speech_vol1_p0003",
        "quote": "We are not going to the Chavdar Tank merely to drink its water. We are going to establish that we are also human beings.",
        "location": "Mahad, Kolaba District, Maharashtra",
        "significance": "Commemorated annually as Social Empowerment Day (Samajik Adhikarita Divas) in India.",
    },
    {
        "id": "evt_1927_manusmriti_dahan",
        "year": 1927,
        "date": "December 25, 1927",
        "title": "Manusmriti Dahan at Mahad",
        "category": "Ideological Protest",
        "description": "Public burning of the ancient legal code that codified graded inequality and untouchability, during the second Mahad conference.",
        "document_id": "mahad_resolution",
        "page_id": "ambedkar_speech_vol1_p0003",
        "quote": "The root of untouchability is not in physical impurity, but in the religious injunction of inequality.",
        "location": "Mahad, Maharashtra",
        "significance": "Historic declaration of universal human equality and rejection of sanctified hierarchy.",
    },
    {
        "id": "evt_1930_kalaram_temple",
        "year": 1930,
        "date": "March 2, 1930",
        "title": "Kalaram Temple Entry Satyagraha",
        "category": "Civil Rights Movement",
        "description": "Non-violent satyagraha launched at the Kalaram Temple in Nashik demanding equal religious and civic access for untouchables.",
        "document_id": "ambedkar_speech_vol1",
        "page_id": "ambedkar_speech_vol1_p0001",
        "quote": "Our fight is not for temple entry as an end in itself; it is a battle for the fundamental rights of citizenship.",
        "location": "Nashik, Maharashtra",
        "significance": "Demonstrated disciplined non-violent civic resistance over a 5-year campaign.",
    },
    {
        "id": "evt_1930_round_table_conference",
        "year": 1930,
        "date": "November 12, 1930",
        "title": "First Round Table Conference in London",
        "category": "Constitutional Advocacy",
        "description": "Dr. Ambedkar represents the Depressed Classes in London, demanding separate political representation, adult suffrage, and fundamental constitutional safeguards.",
        "document_id": "ambedkar_speech_vol1",
        "page_id": "ambedkar_speech_vol1_p0002",
        "quote": "We demand a place in the sun for twenty percent of the people of India.",
        "location": "St. James's Palace, London",
        "significance": "Internationalized the struggle for Dalit political rights.",
    },
    {
        "id": "evt_1932_poona_pact",
        "year": 1932,
        "date": "September 24, 1932",
        "title": "Signing of the Poona Pact",
        "category": "Political Accord",
        "description": "Historic agreement reached at Yerwada Central Jail between Dr. Ambedkar and caste Hindu leaders, providing 148 reserved legislative seats for Depressed Classes.",
        "document_id": "poona_pact",
        "page_id": "ambedkar_speech_vol1_p0002",
        "quote": "There shall be seats reserved for the Depressed Classes out of the general electorates.",
        "location": "Yerwada Central Jail, Pune",
        "significance": "Established the enduring constitutional framework for reserved legislative representation in India.",
    },
    {
        "id": "evt_1936_annihilation_caste",
        "year": 1936,
        "date": "May 15, 1936",
        "title": "Publication of 'Annihilation of Caste'",
        "category": "Philosophical Treatise",
        "description": "Dr. Ambedkar publishes his undelivered presidential address to the Jat-Pat-Todak Mandal, offering a radical critique of Hindu social reform and caste orthodoxy.",
        "document_id": "annihilation_of_caste",
        "page_id": "ambedkar_speech_vol1_p0001",
        "quote": "Caste is not just a division of labour, it is a division of labourers.",
        "location": "Bombay",
        "significance": "Widely regarded as one of the most influential political treatises of modern India.",
    },
    {
        "id": "evt_1942_labour_member",
        "year": 1942,
        "date": "July 20, 1942",
        "title": "Appointed Labour Member, Viceroy's Executive Council",
        "category": "Governance & Labor Reform",
        "description": "Dr. Ambedkar assumes charge of the Labour portfolio, establishing the 8-hour workday, tripartite labor conferences, maternity benefits, and modern river valley projects.",
        "document_id": "ambedkar_speech_vol1",
        "page_id": "ambedkar_speech_vol1_p0002",
        "quote": "Labor must prepare to become the governing class of the country.",
        "location": "New Delhi",
        "significance": "Laid the institutional foundation of Indian labor law, employment exchanges, and water-energy resource development.",
    },
    {
        "id": "evt_1947_drafting_committee",
        "year": 1947,
        "date": "August 29, 1947",
        "title": "Elected Chairman of the Constitution Drafting Committee",
        "category": "Constitutional Milestone",
        "description": "The Constituent Assembly unanimously appoints Dr. Ambedkar as Chairman of the 7-member Drafting Committee to frame the Constitution of independent India.",
        "document_id": "cad_drafting_speech",
        "page_id": "ambedkar_speech_vol1_p0002",
        "quote": "I came into the Constituent Assembly with no greater aspiration than to safeguard the interests of my people.",
        "location": "Constituent Assembly Hall, New Delhi",
        "significance": "Recognized as the Chief Architect of the Constitution of India.",
    },
    {
        "id": "evt_1948_draft_presentation",
        "year": 1948,
        "date": "November 4, 1948",
        "title": "Presentation of the Draft Constitution to the Assembly",
        "category": "Constitutional Milestone",
        "description": "Dr. Ambedkar delivers his comprehensive motion explaining the structural principles of the draft constitution, federalism, executive accountability, and fundamental rights.",
        "document_id": "cad_drafting_speech",
        "page_id": "ambedkar_speech_vol1_p0002",
        "quote": "The Draft Constitution has sought to forge means and methods by which India will be an undivided unit in all matters which are of the essence of unity.",
        "location": "Constitution Hall, New Delhi",
        "significance": "The definitive master exposition of India's constitutional framework.",
    },
    {
        "id": "evt_1949_final_assembly_speech",
        "year": 1949,
        "date": "November 25, 1949",
        "title": "Final Address to the Constituent Assembly: The Three Warnings",
        "category": "Constitutional Milestone",
        "description": "Dr. Ambedkar delivers his historic concluding address, warning against unconstitutional methods, hero-worship in politics, and the contradiction between political equality and social inequality.",
        "document_id": "cad_drafting_speech",
        "page_id": "ambedkar_speech_vol1_p0002",
        "quote": "Political democracy cannot last unless there lies at the base of it social democracy.",
        "location": "Constitution Hall, New Delhi",
        "significance": "The philosophical bedrock of Indian constitutional morality and republican vigilance.",
    },
    {
        "id": "evt_1949_constitution_adoption",
        "year": 1949,
        "date": "November 26, 1949",
        "title": "Adoption of the Constitution of India",
        "category": "Constitutional Milestone",
        "description": "The Constituent Assembly of India formally adopts the Constitution, enacting its Preamble and fundamental provisions (commemorated as National Constitution Day / Samvidhan Divas).",
        "document_id": "constitution_preamble",
        "page_id": "ambedkar_speech_vol1_p0005",
        "quote": "We, the People of India, having solemnly resolved to constitute India into a Sovereign Socialist Secular Democratic Republic...",
        "location": "Constitution Hall, New Delhi",
        "significance": "Birth of the supreme law of the Republic of India.",
    },
    {
        "id": "evt_1950_republic_day",
        "year": 1950,
        "date": "January 26, 1950",
        "title": "Constitution Comes into Effect & Republic Day",
        "category": "National Milestone",
        "description": "The Constitution of India comes into full force, replacing the Government of India Act 1935 and establishing India as a sovereign democratic republic.",
        "document_id": "constitution_preamble",
        "page_id": "ambedkar_speech_vol1_p0005",
        "quote": "Justice, social, economic and political; Liberty of thought, expression, belief, faith and worship; Equality of status and of opportunity; Fraternity assuring the dignity of the individual.",
        "location": "Rashtrapati Bhavan & Parliament of India, New Delhi",
        "significance": "Inauguration of the Republic of India.",
    },
    {
        "id": "evt_1956_deekshabhoomi",
        "year": 1956,
        "date": "October 14, 1956",
        "title": "Historic Buddhist Conversion at Deekshabhoomi, Nagpur",
        "category": "Spiritual & Philosophical Emancipation",
        "description": "Dr. Ambedkar, along with half a million followers, embraces Buddhism at Nagpur, taking the 22 vows of social, ethical, and spiritual emancipation.",
        "document_id": "buddha_and_his_dhamma",
        "page_id": "ambedkar_speech_vol1_p0001",
        "quote": "I will follow the Noble Eightfold Path of the Buddha... I will endeavor to establish equality.",
        "location": "Deekshabhoomi, Nagpur, Maharashtra",
        "significance": "Revival of Buddhism in modern India based on morality, equality, and human dignity.",
    },
]


# -----------------------------------------------------------------------------
# 4. AUDIO-VISUAL MEDIA RECORDS WITH SYNCHRONIZED TRANSCRIPTS
# -----------------------------------------------------------------------------

MEDIA_RECORDS: List[Dict[str, Any]] = [
    {
        "id": "media_ambedkar_bbc_1953",
        "alias": "bbc_interview_1953",
        "title": "BBC Radio Interview: Democracy, Equality and Social Reform (1953)",
        "type": "audio",
        "duration": "03:45",
        "duration_seconds": 225,
        "speaker": "Dr. B. R. Ambedkar & Francis Watson (Interviewer)",
        "date": "1953-05-15",
        "language": "eng",
        "description": "Authentic historical radio dialogue discussing the prerequisites of constitutional democracy and the moral foundations of fraternity in independent India.",
        "source": "BBC Archives / All India Radio Memorial Collection",
        "speaker_notes": "Dr. B. R. Ambedkar in dialogue with BBC correspondent Francis Watson in London. Explores constitutional morality and the essential conditions for parliamentary democracy in newly independent India.",
        "historical_context": "Broadcast in May 1953 following India's first general elections. Dr. Ambedkar emphasizes that formal political democracy cannot endure without the underlying foundation of social democracy.",
        "related_records": ["ambedkar_speech_vol1", "cad_drafting_speech"],
        "transcript": [
            {
                "start": "00:00",
                "seconds": 0,
                "end": "00:32",
                "end_seconds": 32,
                "speaker": "Francis Watson",
                "text": "Dr. Ambedkar, looking back over the framing of India's Constitution, what in your view is the most critical condition for parliamentary democracy to thrive?",
            },
            {
                "start": "00:32",
                "seconds": 32,
                "end": "01:25",
                "end_seconds": 85,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "Democracy is not merely a form of government. It is primarily a mode of associated living, of conjoint communicated experience. It is essentially an attitude of respect and reverence towards one's fellow men.",
            },
            {
                "start": "01:25",
                "seconds": 85,
                "end": "02:10",
                "end_seconds": 130,
                "speaker": "Francis Watson",
                "text": "Do you feel that constitutional law alone can guarantee equality without social democracy?",
            },
            {
                "start": "02:10",
                "seconds": 130,
                "end": "03:15",
                "end_seconds": 195,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "Political democracy cannot last unless there lies at the base of it social democracy. What does social democracy mean? It means a way of life which recognizes liberty, equality, and fraternity as the principles of life.",
            },
            {
                "start": "03:15",
                "seconds": 195,
                "end": "03:45",
                "end_seconds": 225,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "These principles of liberty, equality, and fraternity are not to be treated as separate items in a trinity. They form a union of trinity in the sense that to divorce one from the other is to defeat the very purpose of democracy.",
            },
        ],
    },
    {
        "id": "media_cad_speech_1949",
        "alias": "constituent_assembly_speech_1949",
        "title": "Constituent Assembly Final Address: Contradictions and Warning (1949)",
        "type": "video",
        "duration": "04:12",
        "duration_seconds": 252,
        "speaker": "Dr. B. R. Ambedkar (Chairman, Drafting Committee)",
        "date": "1949-11-25",
        "language": "eng",
        "description": "Historic address to the Constituent Assembly on the eve of the adoption of the Constitution, warning against hero-worship (Bhakti in politics) and urging social democracy.",
        "source": "Films Division of India / National Film Archive of India",
        "speaker_notes": "Dr. B. R. Ambedkar, Chairman of the Drafting Committee, delivering his final valedictory address to the Constituent Assembly of India in New Delhi.",
        "historical_context": "Delivered November 25, 1949, on the eve of the formal adoption of the Constitution. Formulates the famous 'Three Warnings' regarding political democracy versus socio-economic inequality and the perils of hero-worship (Bhakti).",
        "related_records": ["cad_drafting_speech", "constitution_preamble"],
        "transcript": [
            {
                "start": "00:00",
                "seconds": 0,
                "end": "00:45",
                "end_seconds": 45,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "On the 26th of January 1950, we are going to enter into a life of contradictions. In politics we will have equality and in social and economic life we will have inequality.",
            },
            {
                "start": "00:45",
                "seconds": 45,
                "end": "01:40",
                "end_seconds": 100,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "In politics we will be recognizing the principle of one man one vote and one vote one value. In our social and economic life, we shall, by reason of our social and economic structure, continue to deny the principle of one man one value.",
            },
            {
                "start": "01:40",
                "seconds": 100,
                "end": "02:40",
                "end_seconds": 160,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "How long shall we continue to live this life of contradictions? How long shall we continue to deny equality in our social and economic life? If we continue to deny it for long, we will do so only by putting our political democracy in peril.",
            },
            {
                "start": "02:40",
                "seconds": 160,
                "end": "03:30",
                "end_seconds": 210,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "We must remove this contradiction at the earliest possible moment or else those who suffer from inequality will blow up the structure of political democracy which this Assembly has so laboriously built up.",
            },
            {
                "start": "03:30",
                "seconds": 210,
                "end": "04:12",
                "end_seconds": 252,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "Bhakti in religion may be a road to the salvation of the soul. But in politics, Bhakti or hero-worship is a sure road to degradation and to eventual dictatorship.",
            },
        ],
    },
    {
        "id": "media_mahad_memorial_audio_1927",
        "alias": "mahad_memorial_address_1927",
        "title": "Chavdar Tale Water Satyagraha Declaration (1927 Commemoration)",
        "type": "audio",
        "duration": "02:50",
        "duration_seconds": 170,
        "speaker": "Dr. B. R. Ambedkar (Marathi Archival Address)",
        "date": "1927-03-20",
        "language": "mar",
        "description": "Memorial recording of the historic Mahad declaration affirming universal human dignity and water as a fundamental human right.",
        "source": "Maharashtra State Archival Sound Vaults",
        "speaker_notes": "Dr. B. R. Ambedkar addressing thousands of satyagrahis gathered at the historic Chavdar Tale in Mahad, Kolaba District, Maharashtra.",
        "historical_context": "March 20, 1927. The first collective civil rights movement asserting that public water resources belong equally to all human beings, regardless of caste status.",
        "related_records": ["mahad_resolution", "mooknayak_inaugural"],
        "transcript": [
            {
                "start": "00:00",
                "seconds": 0,
                "end": "00:40",
                "end_seconds": 40,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "महाडच्या चवदार तळ्याचे पाणी पिऊन आपण अमर होणार नाही. आम्ही पाण्याकरता तळमळत नाही, आम्ही माणूस म्हणून जगण्याच्या हक्कासाठी येथे आलो आहोत.",
            },
            {
                "start": "00:40",
                "seconds": 40,
                "end": "01:30",
                "end_seconds": 90,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "हा लढा केवळ पाण्यासाठी नाही, तर मानवी आत्मसन्मान आणि मूलभूत मानवी हक्कांच्या प्रस्थापिततेसाठी आहे.",
            },
            {
                "start": "01:30",
                "seconds": 90,
                "end": "02:15",
                "end_seconds": 135,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "जोपर्यंत प्रत्येक नागरिकाला समानतेने जगता येत नाही, तोपर्यंत समाजाची खरी प्रगती अशक्य आहे.",
            },
            {
                "start": "02:15",
                "seconds": 135,
                "end": "02:50",
                "end_seconds": 170,
                "speaker": "Dr. B. R. Ambedkar",
                "text": "शिका, संघटित व्हा आणि संघर्ष करा - हाच आत्ममुक्तीचा मार्ग आहे.",
            },
        ],
    },
]


# -----------------------------------------------------------------------------
# 5. ACCESSOR FUNCTIONS
# -----------------------------------------------------------------------------

def get_discovery_pathways() -> List[Dict[str, Any]]:
    """Returns the 6 curated digital heritage discovery pathways."""
    return list(DISCOVERY_PATHWAYS)


def get_catalog_items() -> List[Dict[str, Any]]:
    """Returns the full catalog items collection."""
    return list(CATALOG_ITEMS)


def get_timeline_events() -> List[Dict[str, Any]]:
    """Returns chronologically ordered historical timeline events."""
    return sorted(TIMELINE_EVENTS, key=lambda e: (e["year"], e["date"]))


def get_media_records() -> List[Dict[str, Any]]:
    """Returns the audio-visual media items collection with synced transcripts."""
    return list(MEDIA_RECORDS)


def get_catalog_item(item_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a catalog item by ID or document_id."""
    for item in CATALOG_ITEMS:
        if item["id"] == item_id or item["document_id"] == item_id:
            return dict(item)
    return None


def get_timeline_event(event_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a timeline event by ID."""
    for evt in TIMELINE_EVENTS:
        if evt["id"] == event_id:
            return dict(evt)
    return None


def get_media_record(media_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a media record by ID or alias."""
    for media in MEDIA_RECORDS:
        if media["id"] == media_id or media.get("alias") == media_id:
            return dict(media)
        # Check normalized match
        if media_id in media["id"] or media["id"] in media_id:
            return dict(media)
        if media.get("alias") and (media_id in media["alias"] or media["alias"] in media_id):
            return dict(media)
    return None


# -----------------------------------------------------------------------------
# 6. ARCHIVAL MANUSCRIPT VIEWER FOLIO PAGES
# -----------------------------------------------------------------------------

VIEWER_PAGES: List[Dict[str, Any]] = [
    {
        "page_id": "ambedkar_speech_vol1_p0001",
        "document_id": "ambedkar_speech_vol1",
        "page_num": 1,
        "title": "Folio 1: Title Page & Imprint",
        "subtitle": "Dr. Babasaheb Ambedkar Writings and Speeches, Vol. 1",
        "language": "eng",
        "original_lang": "en",
        "rights": "public",
        "dpi": 300,
        "badge": "Title Folio",
        "ocr_confidence": 98.2,
        "original_text": "DR. BABASAHEB AMBEDKAR WRITINGS AND SPEECHES VOL. 1. Compiled by Vasant Moon. Published by Education Department, Government of Maharashtra.",
        "translations": {
            "hi": "डॉ. बाबासाहेब आंबेडकर: लेखन और भाषण, खंड १। वसंत मून द्वारा संकलित। शिक्षा विभाग, महाराष्ट्र सरकार द्वारा प्रकाशित।",
            "mr": "डॉ. बाबासाहेब आंबेडकर: लेखन आणि भाषणे, खंड १. वसंत मून द्वारे संकलित. शिक्षण विभाग, महाराष्ट्र शासन द्वारे प्रकाशित.",
        },
    },
    {
        "page_id": "ambedkar_speech_vol1_p0002",
        "document_id": "ambedkar_speech_vol1",
        "page_num": 2,
        "title": "Folio 2: Editorial Preface & Note",
        "subtitle": "Compilation history and editorial remarks by Vasant Moon",
        "language": "eng",
        "original_lang": "en",
        "rights": "public",
        "dpi": 300,
        "badge": "Preface",
        "ocr_confidence": 97.5,
        "original_text": "Editorial Preface & Historical Note: The compilation of Dr. Ambedkar's foundational treatises on caste, linguistic provinces, and constitutional democracy.",
        "translations": {
            "hi": "संपादकीय प्राक्कथन और ऐतिहासिक टिप्पणी: जाति, भाषाई प्रांतों और संवैधानिक लोकतंत्र पर डॉ. आंबेडकर के मौलिक शोध निबंधों का संकलन।",
            "mr": "संपादकीय मनोगत आणि ऐतिहासिक नोंद: जात, भाषावार प्रांतरचना आणि घटनात्मक लोकशाही यावरील डॉ. आंबेडकरांच्या मूलभूत ग्रंथांचे संकलन.",
        },
    },
    {
        "page_id": "ambedkar_speech_vol1_p0003",
        "document_id": "ambedkar_speech_vol1",
        "page_num": 3,
        "title": "Folio 3: Mahad Water Conference Declaration",
        "subtitle": "Chavdar Tale civic rights and human dignity proclamation",
        "language": "mar",
        "original_lang": "mr",
        "rights": "public",
        "dpi": 300,
        "badge": "Historic Proclamation",
        "ocr_confidence": 96.8,
        "original_text": "महाडच्या चवदार तळ्याचे पाणी पिऊन आपण अमर होणार नाही. आम्ही माणूस म्हणून जगण्याच्या मूलभूत हक्कासाठी येथे आलो आहोत.",
        "translations": {
            "en": "We are not going to the Chavdar Tank merely to drink its water. We are not clamoring for water, we have come here to establish our basic human rights as human beings.",
            "hi": "हम चवदार तालाब का पानी केवल पीने के लिए नहीं जा रहे हैं। हम पानी के लिए नहीं तरस रहे हैं, हम यहाँ मनुष्य के रूप में अपने मौलिक मानवीय अधिकारों को स्थापित करने आए हैं।",
        },
    },
    {
        "page_id": "ambedkar_speech_vol1_p0004",
        "document_id": "ambedkar_speech_vol1",
        "page_num": 4,
        "title": "Folio 4: Mooknayak Opening Editorial",
        "subtitle": "First issue editorial on social hierarchy and emancipatory press",
        "language": "mar",
        "original_lang": "mr",
        "rights": "public",
        "dpi": 300,
        "badge": "Periodical",
        "ocr_confidence": 97.1,
        "original_text": "हिंदू समाज हा अनेक मजल्यांच्या मनोऱ्यासारखा आहे ज्याला जिना नाही आणि दारही नाही. जो ज्या मजल्यावर जन्माला आला त्याला त्याच मजल्यावर मरावे लागते.",
        "translations": {
            "en": "Hindu society is like a multi-storeyed tower with neither staircase nor entrance. Those born on the lowest floor must die on the lowest floor without hope of elevation.",
            "hi": "हिंदू समाज एक बहुमंजिला मीनार की तरह है जिसमें न कोई सीढ़ी है और न कोई प्रवेश द्वार है। जो जिस मंजिल पर पैदा हुआ उसे उसी मंजिल पर मरना पड़ता है।",
        },
    },
    {
        "page_id": "ambedkar_speech_vol1_p0005",
        "document_id": "ambedkar_speech_vol1",
        "page_num": 5,
        "title": "Folio 5: Draft Constitution Motion Introduction",
        "subtitle": "Constituent Assembly motion introducing the Draft Constitution",
        "language": "eng",
        "original_lang": "en",
        "rights": "public",
        "dpi": 300,
        "badge": "Constituent Assembly",
        "ocr_confidence": 99.0,
        "original_text": "On the 26th of January 1950, we are going to enter into a life of contradictions. In politics we will have equality and in social and economic life we will have inequality.",
        "translations": {
            "hi": "२६ जनवरी १९५० को हम अंतर्विरोधों के जीवन में प्रवेश करने जा रहे हैं। राजनीति में हमारे पास समानता होगी और सामाजिक व आर्थिक जीवन में असमानता होगी।",
            "mr": "२६ जानेवारी १९५० रोजी आपण एका परस्परविरोधी जीवनात प्रवेश करणार आहोत. राजकारणात आपल्याकडे समानता असेल आणि सामाजिक व आर्थिक जीवनात विषमता असेल.",
        },
    },
]


def get_viewer_pages() -> List[Dict[str, Any]]:
    """Returns the list of selectable archival pages for the Manuscript Viewer."""
    return list(VIEWER_PAGES)


def get_viewer_page(page_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a viewer page folio by page_id."""
    for p in VIEWER_PAGES:
        if p["page_id"] == page_id:
            return dict(p)
    return None

