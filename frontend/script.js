/* ═══════════════════════════════════════════════════════════════════════════
   script.js — Smart Farming AI Advisor
   ─────────────────────────────────────
   Supported languages: en (English) | hi (Hindi) | te (Telugu)
   Language is persisted in localStorage under the key "sf_language".
   ═══════════════════════════════════════════════════════════════════════════ */

"use strict";

// ── Backend base URL ──────────────────────────────────────────────────────────
// ── Backend base URL — override window.SF_API_BASE before this script loads
// to point to a deployed backend without editing source.
const API_BASE = (typeof window !== "undefined" && window.SF_API_BASE)
  ? window.SF_API_BASE.replace(/\/$/, "")
  : "http://localhost:5000";

// ── Valid language codes ──────────────────────────────────────────────────────
const VALID_LANGS = ["en", "hi", "te"];
const DEFAULT_LANG = "en";

// ── Read saved language (ISO code) from localStorage ─────────────────────────
function getSavedLang() {
  const saved = localStorage.getItem("sf_language") || "";
  return VALID_LANGS.includes(saved) ? saved : DEFAULT_LANG;
}

// ── Get currently selected language from the dropdown ────────────────────────
function getCurrentLang() {
  const sel = document.getElementById("language");
  const val = sel ? sel.value : "";
  return VALID_LANGS.includes(val) ? val : DEFAULT_LANG;
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRANSLATIONS — single source of truth for all visible UI text
// Keys used by data-i18n / data-i18n-placeholder attributes in index.html
// ═══════════════════════════════════════════════════════════════════════════════
const T = {

  // ── English ────────────────────────────────────────────────────────────────
  en: {
    // Page / header
    page_title:   "🌾 Smart Farming AI Advisor",
    site_title:   "Smart Farming AI",
    site_tagline: "Powered by IBM Granite & watsonx.ai",
    lang_label:   "🌐 Language:",

    // Tabs
    tab_chat:    "💬 Chat",
    tab_weather: "⛅ Weather",
    tab_market:  "📊 Market Prices",
    tab_crop:    "🌱 Crop Advice",
    tab_pest:    "🐛 Pest Control",

    // Chat tab
    chat_title:       "💬 AI Farming Chatbot",
    chat_subtitle:    "Ask any question about crops, soil, weather, fertilizers or farming practices.",
    quick_label:      "Quick questions:",
    q_rice:           "Rice cultivation",
    q_rice_q:         "How to grow rice in black cotton soil?",
    q_wheat:          "Wheat fertilizer",
    q_wheat_q:        "What fertilizer should I apply for wheat crop?",
    q_faw:            "FAW in maize",
    q_faw_q:          "How to control Fall Armyworm in maize?",
    q_govt:           "Govt schemes",
    q_govt_q:         "What are the government schemes for farmers in India?",
    q_drought:        "Drought management",
    q_drought_q:      "How to manage drought in my farm?",
    welcome_msg:      "Hello! I'm your AI farming assistant. Ask me anything about crops, soil, weather, pests, or farming practices in <strong>English, Hindi or Telugu</strong>.",
    chat_placeholder: "Type your farming question here...",
    btn_send:         "Send",

    // Weather tab
    weather_title:       "⛅ Weather Information",
    weather_subtitle:    "Get current weather and 3-day forecast for your location with farming advice.",
    weather_placeholder: "Enter city / district (e.g. Warangal, Guntur, Pune)",
    btn_get_weather:     "Get Weather",

    // Market tab
    market_title:            "📊 Mandi / Market Prices",
    market_subtitle:         "MSP reference prices (Govt. of India 2024-25) + IBM Granite AI market advisory — 130+ products.",
    market_cat_label:        "Category:",
    cat_all:        "All",    cat_vegetables: "Vegetables",
    cat_fruits:     "Fruits", cat_cereals:    "Cereals",
    cat_pulses:     "Pulses", cat_oilseeds:   "Oilseeds",
    cat_spices:     "Spices", cat_other:      "Other Crops",
    market_crop_placeholder: "Search product (e.g. tomato, apple, wheat)",
    market_state_placeholder:"State (optional, e.g. Andhra Pradesh)",
    market_name_placeholder: "Market / City (optional, e.g. Visakhapatnam)",
    btn_get_prices:          "Get Prices",
    popular_label:           "Popular:",
    loading_market:          "Getting MSP reference and IBM Granite market advisory...",
    lbl_modal_price:         "Modal Price",
    lbl_min_price:           "Min Price",
    lbl_max_price:           "Max Price",
    lbl_markets:             "Mandis",
    lbl_states:              "States",
    lbl_as_of:               "As of",
    lbl_source:              "Source",
    lbl_records:             "Records",
    no_live_data_title:      "⚠️ Live Price Data Unavailable",
    no_live_data_msg:        "Live market price data for this product is not available from the current source.",
    no_live_setup:           "This service uses Government of India MSP data and IBM Granite AI. No external market API is required.",
    err_no_api_key:          "",
    err_no_api_key_hint:     "",
    err_no_records:          "No data available for this product and location.",
    err_no_records_hint:     "Try another product name or check spelling.",
    err_api_unauthorized:    "",
    err_api_timeout:         "The AI advisory service took too long. Please try again.",
    err_api_error:           "An error occurred. Please try again.",
    product_not_found_title: "❌ Product Not Found",
    product_not_found_msg:   "This product is not in the supported catalog. Please try another name.",
    lbl_official_source:     "Reference: e-NAM / APMC portal",
    err_market_empty:        "Please enter a product name or select from the category list.",

    // Crop tab
    crop_title:               "🌱 Crop Recommendation",
    crop_subtitle:            "Get AI-powered crop suggestions based on your soil, season, and location.",
    label_soil:               "Soil Type",
    label_season:             "Season",
    label_location:           "Location / State",
    label_water:              "Water Source",
    crop_location_placeholder:"e.g. Telangana, Punjab, Maharashtra",
    btn_crop_recommend:       "Get Crop Recommendation",
    opt_select_soil:          "-- Select soil type --",
    opt_red_soil:             "Red Soil",
    opt_black_soil:           "Black Cotton Soil",
    opt_alluvial:             "Alluvial Soil",
    opt_sandy:                "Sandy Loam Soil",
    opt_loamy:                "Loamy Soil",
    opt_clay:                 "Clay Soil",
    opt_saline:               "Saline Soil",
    opt_select_season:        "-- Select season --",
    opt_kharif:               "Kharif (June–October)",
    opt_rabi:                 "Rabi (October–March)",
    opt_zaid:                 "Zaid / Summer (March–June)",
    opt_yearround:            "Year-round",
    opt_rainfed:              "Rainfed",
    opt_canal:                "Canal Irrigation",
    opt_borewell:             "Borewell",
    opt_drip:                 "Drip Irrigation",

    // Pest tab
    pest_title:               "🐛 Pest & Disease Control",
    pest_subtitle:            "Describe the pest or disease problem and get AI-powered management advice.",
    label_affected_crop:      "Affected Crop",
    label_problem:            "Problem Description",
    pest_crop_placeholder:    "e.g. Rice, Cotton, Tomato",
    pest_problem_placeholder: "e.g. Yellow leaves, holes in fruit, white insects under leaves",
    btn_pest_control:         "Get Pest Control Advice",

    // Footer
    footer_text: "🌾 Smart Farming AI Advisor | Powered by IBM Granite via watsonx.ai | Data source: KVK / ICAR guidelines | Always verify with your local agricultural extension officer.",

    // Dynamic / JS-generated UI strings
    loading_chat:       "IBM Granite is thinking...",
    loading_weather:    "Fetching weather data...",
    loading_market:     "Fetching market prices...",
    loading_crop:       "Getting crop recommendation from IBM Granite...",
    loading_pest:       "Analyzing the pest/disease problem...",
    thinking_label:     "Thinking...",
    ai_label:           "🤖 AI Advisor",
    you_label:          "👤 You",
    error_label:        "⚠️ Error",
    err_ai_unavailable: "Unable to connect to the AI service. Please try again later.",
    err_no_question:    "Please type a question before sending.",
    err_no_location:    "Please enter a city or district name.",
    err_no_crop:        "Please enter a crop name.",
    err_no_fields:      "Please fill in all required fields.",
    err_server:         "Could not connect to the server. Make sure the backend is running.",
    crop_result_title:  "🌱 AI Crop Recommendation",
    pest_result_title:  "🐛 Pest & Disease Management Advice",
  },

  // ── Hindi ──────────────────────────────────────────────────────────────────
  hi: {
    page_title:   "🌾 स्मार्ट कृषि AI सलाहकार",
    site_title:   "स्मार्ट कृषि AI",
    site_tagline: "IBM Granite और watsonx.ai द्वारा संचालित",
    lang_label:   "🌐 भाषा:",

    tab_chat:    "💬 चैट",
    tab_weather: "⛅ मौसम",
    tab_market:  "📊 बाज़ार भाव",
    tab_crop:    "🌱 फ़सल सलाह",
    tab_pest:    "🐛 कीट नियंत्रण",

    chat_title:       "💬 AI कृषि सहायक",
    chat_subtitle:    "फ़सल, मिट्टी, मौसम, उर्वरक या खेती से जुड़ा कोई भी सवाल पूछें।",
    quick_label:      "त्वरित प्रश्न:",
    q_rice:           "धान की खेती",
    q_rice_q:         "काली कपास मिट्टी में धान कैसे उगाएं?",
    q_wheat:          "गेहूं उर्वरक",
    q_wheat_q:        "गेहूं की फ़सल के लिए कौन सा खाद डालें?",
    q_faw:            "मक्के में FAW",
    q_faw_q:          "मक्के में फ़ॉल आर्मीवर्म को कैसे नियंत्रित करें?",
    q_govt:           "सरकारी योजनाएं",
    q_govt_q:         "भारत में किसानों के लिए कौन सी सरकारी योजनाएं हैं?",
    q_drought:        "सूखा प्रबंधन",
    q_drought_q:      "अपने खेत में सूखे का प्रबंधन कैसे करें?",
    welcome_msg:      "नमस्ते! मैं आपका AI कृषि सहायक हूं। फसल, मिट्टी, मौसम, कीट या खेती की किसी भी जानकारी के बारे में <strong>हिंदी, तेलुगू या अंग्रेज़ी</strong> में पूछें।",
    chat_placeholder: "यहाँ अपना कृषि प्रश्न लिखें...",
    btn_send:         "भेजें",

    weather_title:       "⛅ मौसम जानकारी",
    weather_subtitle:    "अपने स्थान का वर्तमान मौसम और 3 दिन का पूर्वानुमान देखें।",
    weather_placeholder: "शहर / जिला दर्ज करें (जैसे वारंगल, गुंटूर, पुणे)",
    btn_get_weather:     "मौसम देखें",

    market_title:            "📊 मंडी / बाज़ार भाव",
    market_subtitle:         "MSP संदर्भ मूल्य (भारत सरकार 2024-25) + IBM Granite AI बाज़ार सलाह — 130+ उत्पाद।",
    market_cat_label:        "श्रेणी:",
    cat_all:        "सभी",       cat_vegetables: "सब्ज़ियां",
    cat_fruits:     "फल",        cat_cereals:    "अनाज",
    cat_pulses:     "दालें",     cat_oilseeds:   "तिलहन",
    cat_spices:     "मसाले",     cat_other:      "अन्य फ़सलें",
    market_crop_placeholder: "उत्पाद खोजें (जैसे टमाटर, सेब, गेहूं)",
    market_state_placeholder:"राज्य (वैकल्पिक, जैसे आंध्र प्रदेश)",
    market_name_placeholder: "मंडी / शहर (वैकल्पिक, जैसे विशाखापत्तनम)",
    btn_get_prices:          "भाव देखें",
    popular_label:           "लोकप्रिय:",
    loading_market:          "MSP संदर्भ और IBM Granite बाज़ार सलाह प्राप्त हो रही है...",
    lbl_modal_price:         "मोडल मूल्य",
    lbl_min_price:           "न्यूनतम मूल्य",
    lbl_max_price:           "अधिकतम मूल्य",
    lbl_markets:             "मंडियां",
    lbl_states:              "राज्य",
    lbl_as_of:               "तारीख",
    lbl_source:              "स्रोत",
    lbl_records:             "रिकॉर्ड",
    no_live_data_title:      "⚠️ लाइव मूल्य डेटा उपलब्ध नहीं",
    no_live_data_msg:        "इस उत्पाद के लिए वर्तमान स्रोत से लाइव मंडी भाव उपलब्ध नहीं है।",
    no_live_setup:           "यह सेवा भारत सरकार के MSP डेटा और IBM Granite AI का उपयोग करती है।",
    err_no_api_key:          "",
    err_no_api_key_hint:     "",
    err_no_records:          "इस उत्पाद और स्थान के लिए डेटा उपलब्ध नहीं है।",
    err_no_records_hint:     "दूसरा उत्पाद नाम आज़माएं या वर्तनी जांचें।",
    err_api_unauthorized:    "",
    err_api_timeout:         "AI सेवा की प्रतिक्रिया में बहुत समय लगा। कृपया पुनः प्रयास करें।",
    err_api_error:           "एक त्रुटि हुई। कृपया पुनः प्रयास करें।",
    product_not_found_title: "❌ उत्पाद नहीं मिला",
    product_not_found_msg:   "यह उत्पाद समर्थित सूची में नहीं है। कृपया दूसरा नाम आज़माएं।",
    lbl_official_source:     "संदर्भ: e-NAM / APMC पोर्टल",
    err_market_empty:        "कृपया उत्पाद का नाम दर्ज करें या श्रेणी से चुनें।",

    crop_title:               "🌱 फ़सल सुझाव",
    crop_subtitle:            "अपनी मिट्टी, मौसम और स्थान के अनुसार AI-आधारित फ़सल सुझाव पाएं।",
    label_soil:               "मिट्टी का प्रकार",
    label_season:             "मौसम",
    label_location:           "स्थान / राज्य",
    label_water:              "सिंचाई स्रोत",
    crop_location_placeholder:"जैसे तेलंगाना, पंजाब, महाराष्ट्र",
    btn_crop_recommend:       "फ़सल सुझाव पाएं",
    opt_select_soil:          "-- मिट्टी का प्रकार चुनें --",
    opt_red_soil:             "लाल मिट्टी",
    opt_black_soil:           "काली कपास मिट्टी",
    opt_alluvial:             "जलोढ़ मिट्टी",
    opt_sandy:                "बलुई दोमट मिट्टी",
    opt_loamy:                "दोमट मिट्टी",
    opt_clay:                 "चिकनी मिट्टी",
    opt_saline:               "लवणीय मिट्टी",
    opt_select_season:        "-- मौसम चुनें --",
    opt_kharif:               "खरीफ (जून–अक्तूबर)",
    opt_rabi:                 "रबी (अक्तूबर–मार्च)",
    opt_zaid:                 "जायद / ग्रीष्म (मार्च–जून)",
    opt_yearround:            "वर्षभर",
    opt_rainfed:              "वर्षाधारित",
    opt_canal:                "नहर सिंचाई",
    opt_borewell:             "बोरवेल",
    opt_drip:                 "ड्रिप सिंचाई",

    pest_title:               "🐛 कीट एवं रोग नियंत्रण",
    pest_subtitle:            "कीट या रोग की समस्या बताएं और AI-आधारित प्रबंधन सलाह पाएं।",
    label_affected_crop:      "प्रभावित फ़सल",
    label_problem:            "समस्या का विवरण",
    pest_crop_placeholder:    "जैसे धान, कपास, टमाटर",
    pest_problem_placeholder: "जैसे पीली पत्तियां, फल में छेद, सफ़ेद कीड़े",
    btn_pest_control:         "कीट नियंत्रण सलाह पाएं",

    footer_text: "🌾 स्मार्ट कृषि AI सलाहकार | IBM Granite और watsonx.ai द्वारा संचालित | डेटा स्रोत: KVK / ICAR दिशा-निर्देश | हमेशा अपने स्थानीय कृषि विस्तार अधिकारी से सत्यापित करें।",

    loading_chat:       "IBM Granite सोच रहा है...",
    loading_weather:    "मौसम डेटा प्राप्त हो रहा है...",
    loading_market:     "मंडी भाव प्राप्त हो रहे हैं...",
    loading_crop:       "IBM Granite से फ़सल सुझाव प्राप्त हो रहा है...",
    loading_pest:       "कीट/रोग समस्या का विश्लेषण हो रहा है...",
    thinking_label:     "सोच रहा हूं...",
    ai_label:           "🤖 AI सलाहकार",
    you_label:          "👤 आप",
    error_label:        "⚠️ त्रुटि",
    err_ai_unavailable: "AI सेवा से कनेक्ट नहीं हो सका। कृपया बाद में पुनः प्रयास करें।",
    err_no_question:    "भेजने से पहले कृपया एक प्रश्न लिखें।",
    err_no_location:    "कृपया शहर या जिले का नाम दर्ज करें।",
    err_no_crop:        "कृपया फ़सल का नाम दर्ज करें।",
    err_no_fields:      "कृपया सभी आवश्यक फ़ील्ड भरें।",
    err_server:         "सर्वर से कनेक्ट नहीं हो सका। कृपया बैकएंड चल रहा है यह सुनिश्चित करें।",
    crop_result_title:  "🌱 AI फ़सल सुझाव",
    pest_result_title:  "🐛 कीट एवं रोग प्रबंधन सलाह",
  },

  // ── Telugu ─────────────────────────────────────────────────────────────────
  te: {
    page_title:   "🌾 స్మార్ట్ వ్యవసాయ AI సలహాదారు",
    site_title:   "స్మార్ట్ వ్యవసాయ AI",
    site_tagline: "IBM Granite మరియు watsonx.ai ద్వారా నడపబడుతోంది",
    lang_label:   "🌐 భాష:",

    tab_chat:    "💬 చాట్",
    tab_weather: "⛅ వాతావరణం",
    tab_market:  "📊 మార్కెట్ ధరలు",
    tab_crop:    "🌱 పంట సలహా",
    tab_pest:    "🐛 చీడపీడ నియంత్రణ",

    chat_title:       "💬 AI వ్యవసాయ సహాయకుడు",
    chat_subtitle:    "పంటలు, నేల, వాతావరణం, ఎరువులు లేదా వ్యవసాయ పద్ధతులపై ఏదైనా అడగండి.",
    quick_label:      "త్వరిత ప్రశ్నలు:",
    q_rice:           "వరి సాగు",
    q_rice_q:         "నల్లరేగడి నేలలో వరి ఎలా పండించాలి?",
    q_wheat:          "గోధుమ ఎరువు",
    q_wheat_q:        "గోధుమ పంటకు ఏ ఎరువు వేయాలి?",
    q_faw:            "మొక్కజొన్నలో FAW",
    q_faw_q:          "మొక్కజొన్నలో ఫాల్ ఆర్మీవార్మ్ ఎలా నియంత్రించాలి?",
    q_govt:           "ప్రభుత్వ పథకాలు",
    q_govt_q:         "భారతదేశంలో రైతులకు ఏ ప్రభుత్వ పథకాలు ఉన్నాయి?",
    q_drought:        "కరువు నిర్వహణ",
    q_drought_q:      "నా పొలంలో కరువు నిర్వహణ ఎలా చేయాలి?",
    welcome_msg:      "నమస్కారం! నేను మీ AI వ్యవసాయ సహాయకుడిని. పంటలు, నేల, వాతావరణం, చీడపీడలు గురించి <strong>తెలుగు, హిందీ లేదా ఇంగ్లీష్</strong>లో అడగండి.",
    chat_placeholder: "ఇక్కడ మీ వ్యవసాయ ప్రశ్న టైప్ చేయండి...",
    btn_send:         "పంపండి",

    weather_title:       "⛅ వాతావరణ సమాచారం",
    weather_subtitle:    "మీ ప్రాంతం వాతావరణం మరియు 3 రోజుల అంచనా చూడండి.",
    weather_placeholder: "నగరం / జిల్లా నమోదు చేయండి (ఉదా. వరంగల్, గుంటూరు, పుణె)",
    btn_get_weather:     "వాతావరణం చూడండి",

    market_title:            "📊 మండి / మార్కెట్ ధరలు",
    market_subtitle:         "MSP సూచన ధరలు (భారత ప్రభుత్వం 2024-25) + IBM Granite AI మార్కెట్ సలహా — 130+ ఉత్పత్తులు.",
    market_cat_label:        "వర్గం:",
    cat_all:        "అన్నీ",        cat_vegetables: "కూరగాయలు",
    cat_fruits:     "పండ్లు",       cat_cereals:    "ధాన్యాలు",
    cat_pulses:     "పప్పుధాన్యాలు", cat_oilseeds:  "నూనె గింజలు",
    cat_spices:     "మసాలాలు",      cat_other:      "ఇతర పంటలు",
    market_crop_placeholder: "ఉత్పత్తి వెతకండి (ఉదా. టమాటా, యాపిల్, గోధుమ)",
    market_state_placeholder:"రాష్ట్రం (ఐచ్ఛికం, ఉదా. ఆంధ్రప్రదేశ్)",
    market_name_placeholder: "మార్కెట్ / నగరం (ఐచ్ఛికం, ఉదా. విశాఖపట్నం)",
    btn_get_prices:          "ధరలు చూడండి",
    popular_label:           "ప్రముఖ:",
    loading_market:          "MSP సూచన మరియు IBM Granite మార్కెట్ సలహా తీసుకుంటోంది...",
    lbl_modal_price:         "మోడల్ ధర",
    lbl_min_price:           "కనిష్ట ధర",
    lbl_max_price:           "గరిష్ట ధర",
    lbl_markets:             "మండీలు",
    lbl_states:              "రాష్ట్రాలు",
    lbl_as_of:               "తేదీ",
    lbl_source:              "మూలం",
    lbl_records:             "రికార్డులు",
    no_live_data_title:      "⚠️ లైవ్ ధర డేటా అందుబాటులో లేదు",
    no_live_data_msg:        "ఈ ఉత్పత్తికి ప్రస్తుత మూలం నుండి లైవ్ మండి ధర అందుబాటులో లేదు.",
    no_live_setup:           "ఈ సేవ భారత ప్రభుత్వ MSP డేటా మరియు IBM Granite AI ఉపయోగిస్తుంది.",
    err_no_api_key:          "",
    err_no_api_key_hint:     "",
    err_no_records:          "ఈ ఉత్పత్తికి డేటా అందుబాటులో లేదు.",
    err_no_records_hint:     "మరొక ఉత్పత్తి పేరు ప్రయత్నించండి లేదా స్పెల్లింగ్ తనిఖీ చేయండి.",
    err_api_unauthorized:    "",
    err_api_timeout:         "AI సేవ స్పందించడానికి చాలా సమయం పట్టింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    err_api_error:           "ఒక లోపం సంభవించింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    product_not_found_title: "❌ ఉత్పత్తి కనుగొనబడలేదు",
    product_not_found_msg:   "ఈ ఉత్పత్తి మద్దతు జాబితాలో లేదు. దయచేసి మరొక పేరు ప్రయత్నించండి.",
    lbl_official_source:     "సూచన: e-NAM / APMC పోర్టల్",
    err_market_empty:        "దయచేసి ఉత్పత్తి పేరు నమోదు చేయండి లేదా వర్గం నుండి ఎంచుకోండి.",

    crop_title:               "🌱 పంట సిఫారసు",
    crop_subtitle:            "మీ నేల, సీజన్ మరియు స్థానం ఆధారంగా AI పంట సూచనలు పొందండి.",
    label_soil:               "నేల రకం",
    label_season:             "సీజన్",
    label_location:           "స్థానం / రాష్ట్రం",
    label_water:              "నీటి వనరు",
    crop_location_placeholder:"ఉదా. తెలంగాణ, పంజాబ్, మహారాష్ట్ర",
    btn_crop_recommend:       "పంట సిఫారసు పొందండి",
    opt_select_soil:          "-- నేల రకం ఎంచుకోండి --",
    opt_red_soil:             "ఎర్ర నేల",
    opt_black_soil:           "నల్లరేగడి నేల",
    opt_alluvial:             "ఒండ్రు నేల",
    opt_sandy:                "ఇసుక దోమట నేల",
    opt_loamy:                "దోమట నేల",
    opt_clay:                 "బంకమట్టి నేల",
    opt_saline:               "లవణ నేల",
    opt_select_season:        "-- సీజన్ ఎంచుకోండి --",
    opt_kharif:               "ఖరీఫ్ (జూన్–అక్టోబర్)",
    opt_rabi:                 "రబీ (అక్టోబర్–మార్చి)",
    opt_zaid:                 "జాయద్ / వేసవి (మార్చి–జూన్)",
    opt_yearround:            "సంవత్సరం పొడవునా",
    opt_rainfed:              "వర్షాధారిత",
    opt_canal:                "కాలువ నీటిపారుదల",
    opt_borewell:             "బోర్వెల్",
    opt_drip:                 "డ్రిప్ నీటిపారుదల",

    pest_title:               "🐛 చీడపీడ & వ్యాధి నియంత్రణ",
    pest_subtitle:            "చీడపీడ లేదా వ్యాధి సమస్య వివరించండి మరియు AI సలహా పొందండి.",
    label_affected_crop:      "ప్రభావిత పంట",
    label_problem:            "సమస్య వివరణ",
    pest_crop_placeholder:    "ఉదా. వరి, పత్తి, టమాటా",
    pest_problem_placeholder: "ఉదా. పసుపు ఆకులు, పండులో రంధ్రాలు, తెల్లని పురుగులు",
    btn_pest_control:         "చీడపీడ నియంత్రణ సలహా పొందండి",

    footer_text: "🌾 స్మార్ట్ వ్యవసాయ AI సలహాదారు | IBM Granite మరియు watsonx.ai ద్వారా నడపబడుతోంది | డేటా మూలం: KVK / ICAR మార్గదర్శకాలు | ఎల్లప్పుడూ మీ స్థానిక వ్యవసాయ విస్తరణ అధికారితో ధృవీకరించండి.",

    loading_chat:       "IBM Granite ఆలోచిస్తోంది...",
    loading_weather:    "వాతావరణ డేటా తీసుకుంటోంది...",
    loading_market:     "మండి ధరలు తీసుకుంటోంది...",
    loading_crop:       "IBM Granite నుండి పంట సిఫారసు తీసుకుంటోంది...",
    loading_pest:       "చీడపీడ/వ్యాధి సమస్యను విశ్లేషిస్తోంది...",
    thinking_label:     "ఆలోచిస్తోంది...",
    ai_label:           "🤖 AI సలహాదారు",
    you_label:          "👤 మీరు",
    error_label:        "⚠️ లోపం",
    err_ai_unavailable: "AI సేవకు కనెక్ట్ కాలేకపోయాము. దయచేసి తర్వాత మళ్ళీ ప్రయత్నించండి.",
    err_no_question:    "దయచేసి పంపే ముందు ఒక ప్రశ్న టైప్ చేయండి.",
    err_no_location:    "దయచేసి నగరం లేదా జిల్లా పేరు నమోదు చేయండి.",
    err_no_crop:        "దయచేసి పంట పేరు నమోదు చేయండి.",
    err_no_fields:      "దయచేసి అన్ని అవసరమైన ఫీల్డ్‌లను పూరించండి.",
    err_server:         "సర్వర్‌కు కనెక్ట్ కాలేకపోయాము. బ్యాకెండ్ నడుస్తోందని నిర్ధారించుకోండి.",
    crop_result_title:  "🌱 AI పంట సిఫారసు",
    pest_result_title:  "🐛 చీడపీడ & వ్యాధి నిర్వహణ సలహా",
  },
};

// Helper: get translation value for current language, falling back to English
function tr(key) {
  const lang = getCurrentLang();
  return (T[lang] && T[lang][key] !== undefined) ? T[lang][key]
       : (T.en[key] !== undefined)               ? T.en[key]
       : key;
}

// ═══════════════════════════════════════════════════════════════════════════════
// APPLY TRANSLATIONS TO THE PAGE
// ═══════════════════════════════════════════════════════════════════════════════
function applyLanguage(lang) {
  if (!VALID_LANGS.includes(lang)) lang = DEFAULT_LANG;

  const map = T[lang];

  // <html lang="…">
  document.getElementById("htmlRoot").setAttribute("lang", lang);

  // Page <title>
  document.title = map.page_title || T.en.page_title;

  // All elements with data-i18n (text content)
  // NOTE: welcome_msg contains HTML — handle separately below
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key === "welcome_msg") return;      // handled below
    if (key === "footer_text") return;      // contains HTML entities, skip innerHTML
    const val = (map[key] !== undefined) ? map[key] : (T.en[key] !== undefined ? T.en[key] : null);
    if (val !== null) el.textContent = val;
  });

  // Footer — set as textContent (safe)
  const footerEl = document.querySelector("[data-i18n='footer_text']");
  if (footerEl) footerEl.textContent = map.footer_text || T.en.footer_text;

  // Welcome message — uses innerHTML (trusted static strings only)
  const welcomeEl = document.querySelector("[data-i18n='welcome_msg']");
  if (welcomeEl) welcomeEl.innerHTML = map.welcome_msg || T.en.welcome_msg;

  // All elements with data-i18n-placeholder
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.getAttribute("data-i18n-placeholder");
    const val = (map[key] !== undefined) ? map[key] : (T.en[key] !== undefined ? T.en[key] : null);
    if (val !== null) el.placeholder = val;
  });

  // Quick-buttons: update label AND the data-q query string used when clicked
  document.querySelectorAll(".quick-btn[data-qkey]").forEach((btn) => {
    const qkey  = btn.getAttribute("data-qkey");
    const label = (map[qkey]         !== undefined) ? map[qkey]         : (T.en[qkey]         || btn.textContent);
    const query = (map[qkey + "_q"]  !== undefined) ? map[qkey + "_q"]  : (T.en[qkey + "_q"]  || "");
    btn.textContent = label;
    btn.setAttribute("data-q", query);
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
// INITIALISE — restore saved language and wire up the selector
// ═══════════════════════════════════════════════════════════════════════════════
(function init() {
  const savedLang = getSavedLang();
  const sel = document.getElementById("language");
  if (sel) sel.value = savedLang;
  applyLanguage(savedLang);

  sel.addEventListener("change", (e) => {
    const chosen = VALID_LANGS.includes(e.target.value) ? e.target.value : DEFAULT_LANG;
    localStorage.setItem("sf_language", chosen);
    applyLanguage(chosen);
  });
})();

// ═══════════════════════════════════════════════════════════════════════════════
// TAB NAVIGATION
// ═══════════════════════════════════════════════════════════════════════════════
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => {
      t.classList.remove("active");
      t.setAttribute("aria-selected", "false");
    });
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    btn.setAttribute("aria-selected", "true");
    const panel = document.getElementById(`tab-${btn.dataset.tab}`);
    if (panel) panel.classList.add("active");
  });
});

// ── Chat character counter ────────────────────────────────────────────────────
const chatInput = document.getElementById("chatInput");
const charCount = document.getElementById("charCount");

chatInput.addEventListener("input", () => {
  const len = chatInput.value.length;
  charCount.textContent = `${len} / 1000`;
  charCount.style.color = len > 900 ? "#c62828" : "";
});

chatInput.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") sendChat();
});

// ── Quick question buttons ────────────────────────────────────────────────────
document.querySelectorAll(".quick-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const q = btn.getAttribute("data-q") || "";
    if (!q.trim()) return;
    chatInput.value = q;
    charCount.textContent = `${q.length} / 1000`;
    sendChat();
  });
});

// ── Market category chips — rendered dynamically ──────────────────────────────
// Full product catalog (mirrors PRODUCT_CATALOG in market.py)
const MARKET_CATALOG = {
  vegetables: ["tomato","potato","onion","brinjal","cabbage","cauliflower","carrot","radish","beetroot","beans","french beans","cluster beans","okra","green peas","green chilli","capsicum","bell pepper","bitter gourd","bottle gourd","ridge gourd","snake gourd","sponge gourd","ash gourd","pumpkin","cucumber","drumstick","spinach","amaranth","coriander","mint","fenugreek leaves","curry leaves","sweet corn","garlic","ginger","sweet potato","raw banana","raw mango"],
  fruits:     ["apple","banana","mango","orange","mandarin","lemon","papaya","pomegranate","grapes","watermelon","muskmelon","guava","pineapple","jackfruit","custard apple","sapota","pears","peach","plum","strawberry","litchi","kiwi","dragon fruit","avocado","coconut","amla","fig","dates","ber"],
  cereals:    ["rice","wheat","maize","barley","bajra","jowar","ragi","oats"],
  pulses:     ["gram","arhar","moong","urad","masoor","peas","rajma"],
  oilseeds:   ["groundnut","soybean","sunflower","sesame","mustard","castor","linseed"],
  spices:     ["chilli","turmeric","cumin","coriander seed","black pepper","cardamom","clove","fennel","fenugreek seed"],
  other:      ["cotton","sugarcane","tobacco","jute","tea","coffee","rubber"],
};

// Display names for chips (short form for UI)
const CHIP_DISPLAY = {
  en: {
    tomato:"Tomato",potato:"Potato",onion:"Onion",brinjal:"Brinjal",cabbage:"Cabbage",cauliflower:"Cauliflower",carrot:"Carrot",radish:"Radish",beetroot:"Beetroot",beans:"Beans","french beans":"Fr. Beans","cluster beans":"Cluster Beans",okra:"Lady Finger","green peas":"Green Peas","green chilli":"Green Chilli",capsicum:"Capsicum","bell pepper":"Bell Pepper","bitter gourd":"Bitter Gourd","bottle gourd":"Bottle Gourd","ridge gourd":"Ridge Gourd","snake gourd":"Snake Gourd","sponge gourd":"Sponge Gourd","ash gourd":"Ash Gourd",pumpkin:"Pumpkin",cucumber:"Cucumber",drumstick:"Drumstick",spinach:"Spinach",amaranth:"Amaranth",coriander:"Coriander",mint:"Mint","fenugreek leaves":"Fenugreek","curry leaves":"Curry Leaf","sweet corn":"Sweet Corn",garlic:"Garlic",ginger:"Ginger","sweet potato":"Sweet Potato","raw banana":"Raw Banana","raw mango":"Raw Mango",
    apple:"Apple",banana:"Banana",mango:"Mango",orange:"Orange",mandarin:"Mandarin",lemon:"Lemon",papaya:"Papaya",pomegranate:"Pomegranate",grapes:"Grapes",watermelon:"Watermelon",muskmelon:"Muskmelon",guava:"Guava",pineapple:"Pineapple",jackfruit:"Jackfruit","custard apple":"Custard Apple",sapota:"Sapota",pears:"Pears",peach:"Peach",plum:"Plum",strawberry:"Strawberry",litchi:"Litchi",kiwi:"Kiwi","dragon fruit":"Dragon Fruit",avocado:"Avocado",coconut:"Coconut",amla:"Amla",fig:"Fig",dates:"Dates",ber:"Ber",
    rice:"Rice",wheat:"Wheat",maize:"Maize",barley:"Barley",bajra:"Bajra",jowar:"Jowar",ragi:"Ragi",oats:"Oats",
    gram:"Gram",arhar:"Arhar/Tur",moong:"Moong",urad:"Urad",masoor:"Masoor",peas:"Peas",rajma:"Rajma",
    groundnut:"Groundnut",soybean:"Soybean",sunflower:"Sunflower",sesame:"Sesame",mustard:"Mustard",castor:"Castor",linseed:"Linseed",
    chilli:"Chilli",turmeric:"Turmeric",cumin:"Cumin","coriander seed":"Coriander Seed","black pepper":"Black Pepper",cardamom:"Cardamom",clove:"Clove",fennel:"Fennel","fenugreek seed":"Fenugreek Seed",
    cotton:"Cotton",sugarcane:"Sugarcane",tobacco:"Tobacco",jute:"Jute",tea:"Tea",coffee:"Coffee",rubber:"Rubber",
  },
  hi: {
    tomato:"टमाटर",potato:"आलू",onion:"प्याज़",brinjal:"बैंगन",cabbage:"पत्तागोभी",cauliflower:"फूलगोभी",carrot:"गाजर",radish:"मूली",beetroot:"चुकंदर",beans:"बीन्स","french beans":"फ्रेंच बीन्स","cluster beans":"ग्वार फली",okra:"भिंडी","green peas":"हरी मटर","green chilli":"हरी मिर्च",capsicum:"शिमला मिर्च","bell pepper":"शिमला मिर्च","bitter gourd":"करेला","bottle gourd":"लौकी","ridge gourd":"तोरी","snake gourd":"चिचिंडा","sponge gourd":"तुरई","ash gourd":"पेठा",pumpkin:"कद्दू",cucumber:"खीरा",drumstick:"सहजन",spinach:"पालक",amaranth:"चौलाई",coriander:"धनिया",mint:"पुदीना","fenugreek leaves":"मेथी","curry leaves":"कड़ी पत्ता","sweet corn":"मक्का",garlic:"लहसुन",ginger:"अदरक","sweet potato":"शकरकंद","raw banana":"कच्चा केला","raw mango":"कच्चा आम",
    apple:"सेब",banana:"केला",mango:"आम",orange:"संतरा",mandarin:"मंदारिन",lemon:"नींबू",papaya:"पपीता",pomegranate:"अनार",grapes:"अंगूर",watermelon:"तरबूज़",muskmelon:"खरबूजा",guava:"अमरूद",pineapple:"अनानास",jackfruit:"कटहल","custard apple":"सीताफल",sapota:"चीकू",pears:"नाशपाती",peach:"आड़ू",plum:"आलूबुखारा",strawberry:"स्ट्रॉबेरी",litchi:"लीची",kiwi:"कीवी","dragon fruit":"ड्रैगन फ्रूट",avocado:"एवोकाडो",coconut:"नारियल",amla:"आंवला",fig:"अंजीर",dates:"खजूर",ber:"बेर",
    rice:"चावल",wheat:"गेहूं",maize:"मक्का",barley:"जौ",bajra:"बाजरा",jowar:"ज्वार",ragi:"रागी",oats:"जई",
    gram:"चना",arhar:"अरहर/तूर",moong:"मूंग",urad:"उड़द",masoor:"मसूर",peas:"मटर",rajma:"राजमा",
    groundnut:"मूंगफली",soybean:"सोयाबीन",sunflower:"सूरजमुखी",sesame:"तिल",mustard:"सरसों",castor:"अरंडी",linseed:"अलसी",
    chilli:"मिर्च",turmeric:"हल्दी",cumin:"जीरा","coriander seed":"धनिया बीज","black pepper":"काली मिर्च",cardamom:"इलायची",clove:"लौंग",fennel:"सौंफ","fenugreek seed":"मेथी दाना",
    cotton:"कपास",sugarcane:"गन्ना",tobacco:"तंबाकू",jute:"जूट",tea:"चाय",coffee:"कॉफी",rubber:"रबर",
  },
  te: {
    tomato:"టమాటా",potato:"ఆలుగడ్డ",onion:"ఉల్లిపాయ",brinjal:"వంకాయ",cabbage:"క్యాబేజీ",cauliflower:"కాలీఫ్లవర్",carrot:"క్యారట్",radish:"ముల్లంగి",beetroot:"బీట్‌రూట్",beans:"చిక్కుళ్ళు","french beans":"ఫ్రెంచ్ బీన్స్","cluster beans":"గోర్చిక్కుడు",okra:"బెండకాయ","green peas":"పచ్చి బఠానీ","green chilli":"పచ్చి మిర్చి",capsicum:"క్యాప్సికమ్","bell pepper":"క్యాప్సికమ్","bitter gourd":"కాకరకాయ","bottle gourd":"సొరకాయ","ridge gourd":"బీరకాయ","snake gourd":"పొట్లకాయ","sponge gourd":"నేతి బీరకాయ","ash gourd":"బుడమ కాయ",pumpkin:"గుమ్మడికాయ",cucumber:"దోసకాయ",drumstick:"మునగకాయ",spinach:"పాలకూర",amaranth:"తోటకూర",coriander:"కొత్తిమీర",mint:"పుదీనా","fenugreek leaves":"మెంతిమూ","curry leaves":"కరివేపాకు","sweet corn":"మొక్కజొన్న",garlic:"వెల్లుల్లి",ginger:"అల్లం","sweet potato":"చేనేత","raw banana":"అరటికాయ","raw mango":"మామిడికాయ",
    apple:"యాపిల్",banana:"అరటిపండు",mango:"మామిడి",orange:"నారింజ",mandarin:"మాండరిన్",lemon:"నిమ్మకాయ",papaya:"బొప్పాయి",pomegranate:"దానిమ్మ",grapes:"ద్రాక్ష",watermelon:"పుచ్చకాయ",muskmelon:"ఖర్బూజా",guava:"జామ",pineapple:"అనాసపండు",jackfruit:"పనసపండు","custard apple":"సీతాఫలం",sapota:"సపోట",pears:"నాసపండు",peach:"పీచు",plum:"ప్లమ్",strawberry:"స్ట్రాబెర్రీ",litchi:"లిచీ",kiwi:"కివి","dragon fruit":"డ్రాగన్ ఫ్రూట్",avocado:"అవకాడో",coconut:"కొబ్బరి",amla:"ఉసిరికాయ",fig:"అత్తి",dates:"ఖర్జూరం",ber:"రేగిపండు",
    rice:"వరి",wheat:"గోధుమ",maize:"మొక్కజొన్న",barley:"బార్లీ",bajra:"సజ్జ",jowar:"జొన్న",ragi:"రాగి",oats:"వోట్స్",
    gram:"శెనగ",arhar:"కంది పప్పు",moong:"పెసర్లు",urad:"మినుములు",masoor:"మసూర్",peas:"బఠానీ",rajma:"రాజ్మా",
    groundnut:"వేరుశనగ",soybean:"సోయాబీన్",sunflower:"పొద్దుతిరుగుడు",sesame:"నువ్వులు",mustard:"ఆవాలు",castor:"ఆముదం",linseed:"అవిసె",
    chilli:"మిర్చి",turmeric:"పసుపు",cumin:"జీలకర్ర","coriander seed":"కొత్తిమీర విత్తు","black pepper":"మిరియాలు",cardamom:"ఏలకులు",clove:"లవంగాలు",fennel:"సోంపు","fenugreek seed":"మెంతులు",
    cotton:"పత్తి",sugarcane:"చెరకు",tobacco:"పొగాకు",jute:"జూట్",tea:"తేయాకు",coffee:"కాఫీ",rubber:"రబ్బర్",
  },
};

// Default chips shown when category = 'all'
const DEFAULT_CHIPS = ["tomato","potato","onion","apple","banana","mango","rice","wheat","maize","groundnut","chilli","turmeric"];

function getChipDisplay(key) {
  const lang = getCurrentLang();
  return (CHIP_DISPLAY[lang] && CHIP_DISPLAY[lang][key]) || CHIP_DISPLAY.en[key] || key;
}

function renderMarketChips(category = "all") {
  const area = document.getElementById("marketChipsArea");
  if (!area) return;

  let keys;
  if (category === "all") {
    keys = DEFAULT_CHIPS;
    area.innerHTML = `
      <div class="chips-section">
        <span class="chips-section-label">${escHtml(tr("popular_label"))}</span>
        <div class="chip-wrap">${keys.map(k =>
          `<button class="market-chip" onclick="marketChipClick('${k}')">${escHtml(getChipDisplay(k))}</button>`
        ).join("")}</div>
      </div>`;
  } else {
    keys = MARKET_CATALOG[category] || [];
    area.innerHTML = `
      <div class="chips-section">
        <span class="chips-section-label">${escHtml(tr("cat_" + category))}</span>
        <div class="chip-wrap">${keys.map(k =>
          `<button class="market-chip" onclick="marketChipClick('${k}')">${escHtml(getChipDisplay(k))}</button>`
        ).join("")}</div>
      </div>`;
  }
}

function marketChipClick(key) {
  const input = document.getElementById("marketCrop");
  if (input) input.value = key;
  hideSuggestions();
  fetchMarket();
}

function onMarketCategoryChange() {
  const cat = document.getElementById("marketCategory").value;
  renderMarketChips(cat);
}

// ── Autocomplete ──────────────────────────────────────────────────────────────
let _acResults = [];
let _acIndex   = -1;

async function onMarketSearchInput() {
  const q = (document.getElementById("marketCrop").value || "").trim();
  const sugEl = document.getElementById("marketSuggestions");
  if (!q || q.length < 2) { hideSuggestions(); return; }

  try {
    const resp = await fetch(`${API_BASE}/api/market/search?q=${encodeURIComponent(q)}&limit=8`);
    const data = await resp.json();
    _acResults = data.results || [];
    _acIndex   = -1;

    if (!_acResults.length) { hideSuggestions(); return; }

    sugEl.innerHTML = _acResults.map((r, i) =>
      `<li data-idx="${i}" onclick="acSelect(${i})">
        ${escHtml(r.display)}
        <span class="ac-cat">${escHtml(tr("cat_" + r.category))}</span>
      </li>`
    ).join("");
    sugEl.style.display = "block";
  } catch {
    hideSuggestions();
  }
}

function onMarketSearchKeydown(e) {
  const sugEl = document.getElementById("marketSuggestions");
  if (sugEl.style.display === "none" || !_acResults.length) {
    if (e.key === "Enter") fetchMarket();
    return;
  }
  if (e.key === "ArrowDown") {
    e.preventDefault();
    _acIndex = Math.min(_acIndex + 1, _acResults.length - 1);
    highlightAc(_acIndex);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    _acIndex = Math.max(_acIndex - 1, 0);
    highlightAc(_acIndex);
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (_acIndex >= 0) acSelect(_acIndex); else fetchMarket();
  } else if (e.key === "Escape") {
    hideSuggestions();
  }
}

function highlightAc(idx) {
  document.querySelectorAll("#marketSuggestions li").forEach((li, i) => {
    li.classList.toggle("selected", i === idx);
  });
}

function acSelect(idx) {
  if (_acResults[idx]) {
    document.getElementById("marketCrop").value = _acResults[idx].key;
  }
  hideSuggestions();
  fetchMarket();
}

function hideSuggestions() {
  const el = document.getElementById("marketSuggestions");
  if (el) el.style.display = "none";
}

// Hide autocomplete when clicking outside
document.addEventListener("click", (e) => {
  if (!e.target.closest(".market-search-row")) hideSuggestions();
});

// Render default chips on page load
renderMarketChips("all");

// ═══════════════════════════════════════════════════════════════════════════════
// 1. CHAT
// ═══════════════════════════════════════════════════════════════════════════════
function appendMessage(role, text) {
  const chatWindow = document.getElementById("chatWindow");
  // Remove welcome screen on first message
  const welcome = chatWindow.querySelector(".chat-welcome");
  if (welcome) welcome.remove();

  const msgDiv  = document.createElement("div");
  msgDiv.className = `msg ${role}`;

  const label = document.createElement("div");
  label.className = "msg-label";
  if (role === "user")  label.textContent = tr("you_label");
  else if (role === "ai") label.textContent = tr("ai_label");
  else label.textContent = tr("error_label");

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = safeFormat(text);

  msgDiv.appendChild(label);
  msgDiv.appendChild(bubble);
  chatWindow.appendChild(msgDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function appendTypingIndicator() {
  const chatWindow = document.getElementById("chatWindow");
  const div = document.createElement("div");
  div.className = "msg ai";
  div.id = "typing-indicator";
  div.innerHTML = `
    <div class="msg-label">${escHtml(tr("ai_label"))}</div>
    <div class="msg-bubble" style="display:flex;align-items:center;gap:8px;">
      <div class="spinner"></div> ${escHtml(tr("thinking_label"))}
    </div>`;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

async function sendChat() {
  const question = chatInput.value.trim();
  if (!question) {
    chatInput.focus();
    return;
  }

  const language = getCurrentLang();
  const sendBtn  = document.getElementById("sendBtn");

  sendBtn.disabled = true;
  sendBtn.querySelector(".btn-text").classList.add("hidden");
  sendBtn.querySelector(".btn-loader").classList.remove("hidden");

  appendMessage("user", question);
  chatInput.value = "";
  charCount.textContent = "0 / 1000";
  appendTypingIndicator();

  try {
    const resp = await fetch(`${API_BASE}/api/chat`, {
      method:  "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body:    JSON.stringify({ question, language, location: "India" }),
    });
    const data = await resp.json();
    removeTypingIndicator();
    if (!resp.ok || data.error) {
      appendMessage("error", data.error || tr("err_ai_unavailable"));
    } else {
      appendMessage("ai", data.answer);
    }
  } catch {
    removeTypingIndicator();
    appendMessage("error", tr("err_server"));
  } finally {
    sendBtn.disabled = false;
    sendBtn.querySelector(".btn-text").classList.remove("hidden");
    sendBtn.querySelector(".btn-loader").classList.add("hidden");
    chatInput.focus();
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 2. WEATHER
// ═══════════════════════════════════════════════════════════════════════════════
async function fetchWeather() {
  const location = document.getElementById("weatherLocation").value.trim();
  const language = getCurrentLang();
  const resultEl = document.getElementById("weatherResult");

  if (!location) {
    resultEl.innerHTML = renderError(tr("err_no_location"));
    return;
  }

  resultEl.innerHTML = renderLoading(tr("loading_weather"));

  try {
    const resp = await fetch(
      `${API_BASE}/api/weather?location=${encodeURIComponent(location)}&language=${encodeURIComponent(language)}`
    );
    const data = await resp.json();
    if (!resp.ok || data.error) {
      resultEl.innerHTML = renderError(data.error || tr("err_ai_unavailable"));
      return;
    }

    // Build season tips list
    const tipsHTML = (data.tips || []).map(t =>
      `<li>${escHtml(t)}</li>`
    ).join("");

    // Build stored climate data block if available
    let storedBlock = "";
    if (data.stored_data) {
      const sd = data.stored_data;
      storedBlock = `
        <div class="weather-stored-data">
          <div class="stored-label">📊 ${escHtml(sd.data_label || "Stored typical climate data")}</div>
          <div class="weather-grid">
            <div class="wg-item"><span class="wg-label">🌡️ Temp</span><span class="wg-val">${sd.temp_min_c}°C – ${sd.temp_max_c}°C</span></div>
            <div class="wg-item"><span class="wg-label">💧 Humidity</span><span class="wg-val">~${sd.humidity_pct}%</span></div>
            <div class="wg-item"><span class="wg-label">🌧️ Typical Rain</span><span class="wg-val">~${sd.typical_rain_mm} mm</span></div>
            <div class="wg-item"><span class="wg-label">☁️ Condition</span><span class="wg-val">${escHtml(sd.condition)}</span></div>
          </div>
          ${sd.major_crops ? `<div class="wg-crops">🌾 Major crops: ${escHtml(sd.major_crops)}</div>` : ""}
          ${sd.soil_type   ? `<div class="wg-soil">🪨 Soil: ${escHtml(sd.soil_type)}</div>` : ""}
        </div>`;
    } else if (data.note) {
      storedBlock = `<div class="weather-meta" style="color:#888;">${escHtml(data.note)}</div>`;
    }

    resultEl.innerHTML = `
      <div class="weather-card">
        <div class="weather-current">
          <div class="weather-location">📍 ${escHtml(data.location)}</div>
          <div class="weather-main">
            <div class="weather-temp">🌾 ${escHtml(data.season)} Season</div>
            <div class="weather-condition">${escHtml(data.month_context || "")}</div>
          </div>
        </div>
        <div class="notice-box">⚠️ ${escHtml(data.notice)}</div>
        ${storedBlock}
        <div class="weather-advice">
          <h4>🤖 IBM Granite AI Advisory</h4>
          ${safeFormat(data.ai_advisory || data.advice || "")}
        </div>
        ${tipsHTML ? `<div class="weather-tips"><strong>🌱 Seasonal Farming Tips:</strong><ul>${tipsHTML}</ul></div>` : ""}
        <div class="weather-source" style="font-size:.8rem;color:#777;margin-top:8px;">
          ${escHtml(data.advisory_source || "")}
        </div>
      </div>`;
  } catch (err) {
    resultEl.innerHTML = renderError(tr("err_server"));
  }
}

document.getElementById("weatherLocation").addEventListener("keydown", (e) => {
  if (e.key === "Enter") fetchWeather();
});

// ═══════════════════════════════════════════════════════════════════════════════
// 3. MARKET PRICES
// ═══════════════════════════════════════════════════════════════════════════════
async function fetchMarket() {
  hideSuggestions();
  const crop     = (document.getElementById("marketCrop").value || "").trim();
  const state    = (document.getElementById("marketState").value || "").trim();
  const market   = (document.getElementById("marketName")?.value || "").trim();
  const language = getCurrentLang();
  const resultEl = document.getElementById("marketResult");

  if (!crop) {
    resultEl.innerHTML = renderError(tr("err_market_empty"));
    return;
  }

  resultEl.innerHTML = renderLoading(tr("loading_market"));

  try {
    const resp = await fetch(`${API_BASE}/api/market`, {
      method:  "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body:    JSON.stringify({ crop, state: state || null, market: market || null, language }),
    });
    const data = await resp.json();

    if (!resp.ok) {
      resultEl.innerHTML = renderError(data.error || tr("err_server"));
      return;
    }

    if (data.success === true) {
      // ── MSP block ────────────────────────────────────────────────────
      const mspBlock = data.has_msp
        ? `<div class="mlc-row">
             <div class="lbl">📊 Govt. MSP (Floor Price)</div>
             <div class="val mlc-modal">₹${data.msp_price} <small>/${escHtml(data.unit)}</small></div>
           </div>
           <div class="mlc-row">
             <div class="lbl">📅 MSP Season</div>
             <div class="val">${escHtml(data.msp_season || "")}</div>
           </div>`
        : `<div class="mlc-row">
             <div class="lbl">📊 MSP</div>
             <div class="val" style="color:#e65100;">${escHtml(data.msp_note || "No government MSP for this product.")}</div>
           </div>`;

      // ── Sample mandi data block ───────────────────────────────────────
      let mandiBlock = "";
      if (data.mandi_data && data.mandi_data.length > 0) {
        const rows = data.mandi_data.map(m => `
          <tr>
            <td>${escHtml(m.market)}</td>
            <td>${escHtml(m.state)}</td>
            <td>₹${m.min_price}</td>
            <td>₹${m.max_price}</td>
            <td><strong>₹${m.modal_price}</strong></td>
            <td>${escHtml(m.date_label)}</td>
          </tr>`).join("");
        mandiBlock = `
          <div class="mandi-table-wrap">
            <div class="mandi-label">📋 ${escHtml(data.data_label || "Stored sample mandi data — NOT live prices")}</div>
            <table class="mandi-table">
              <thead><tr><th>Market</th><th>State</th><th>Min ₹</th><th>Max ₹</th><th>Modal ₹</th><th>Period</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
            ${data.mandi_data[0]?.note ? `<div class="mandi-note">${escHtml(data.mandi_data[0].note)}</div>` : ""}
          </div>`;
      } else if (data.mandi_note) {
        mandiBlock = `<div class="mandi-empty">${escHtml(data.mandi_note)}</div>`;
      }

      resultEl.innerHTML = `
        <div class="market-live-card">
          <div class="mlc-header">
            <span class="mlc-name">${escHtml(data.display)}</span>
            <span class="mlc-cat">${escHtml(tr("cat_" + data.category))}</span>
          </div>
          <div class="notice-box">⚠️ ${escHtml(data.notice)}</div>
          <div class="mlc-rows">${mspBlock}</div>
          ${mandiBlock}
          <div class="ai-response" style="margin-top:12px;">
            <h4>🤖 IBM Granite Market Advisory</h4>
            <div class="response-text">${safeFormat(data.ai_advisory || "")}</div>
          </div>
          <div class="mlc-source" style="margin-top:8px;">
            📋 Source: ${escHtml(data.data_source || "Govt. of India CCEA MSP 2024-25 + IBM Granite AI")}
          </div>
        </div>`;

    } else if (data.error_type === "product_not_found") {
      // ── Product not in catalog ───────────────────────────────────────
      resultEl.innerHTML = `
        <div class="market-nodata-card">
          <h4>${escHtml(tr("product_not_found_title"))}</h4>
          <p>${escHtml(tr("product_not_found_msg"))}</p>
          <p style="font-size:.85rem;color:#666;">${escHtml(data.message || "")}</p>
        </div>`;

    } else {
      resultEl.innerHTML = renderError(data.message || tr("err_server"));
    }

  } catch (err) {
    resultEl.innerHTML = renderError(tr("err_server"));
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 4. CROP RECOMMENDATION
// ═══════════════════════════════════════════════════════════════════════════════
async function fetchCropRecommend() {
  const soilType = document.getElementById("soilType").value;
  const season   = document.getElementById("season").value;
  const location = document.getElementById("cropLocation").value.trim() || "India";
  const water    = document.getElementById("waterSource").value;
  const language = getCurrentLang();
  const resultEl = document.getElementById("cropResult");

  if (!soilType || !season) {
    resultEl.innerHTML = renderError(tr("err_no_fields"));
    return;
  }

  resultEl.innerHTML = renderLoading(tr("loading_crop"));

  try {
    const resp = await fetch(`${API_BASE}/api/crop-recommend`, {
      method:  "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body:    JSON.stringify({ soil_type: soilType, season, location, water, language }),
    });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      resultEl.innerHTML = renderError(data.error || tr("err_ai_unavailable"));
      return;
    }
    resultEl.innerHTML = `
      <div class="ai-response">
        <h4>${escHtml(tr("crop_result_title"))}</h4>
        <div class="response-text">${safeFormat(data.recommendation)}</div>
      </div>`;
  } catch (err) {
    resultEl.innerHTML = renderError(tr("err_server"));
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 5. PEST & DISEASE CONTROL
// ═══════════════════════════════════════════════════════════════════════════════
async function fetchPestControl() {
  const crop     = document.getElementById("pestCrop").value.trim();
  const problem  = document.getElementById("pestProblem").value.trim();
  const language = getCurrentLang();
  const resultEl = document.getElementById("pestResult");

  if (!crop || !problem) {
    resultEl.innerHTML = renderError(tr("err_no_fields"));
    return;
  }

  resultEl.innerHTML = renderLoading(tr("loading_pest"));

  try {
    const resp = await fetch(`${API_BASE}/api/pest-control`, {
      method:  "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body:    JSON.stringify({ crop, problem, language, location: "India" }),
    });
    const data = await resp.json();
    if (!resp.ok || data.error) {
      resultEl.innerHTML = renderError(data.error || tr("err_ai_unavailable"));
      return;
    }
    resultEl.innerHTML = `
      <div class="ai-response">
        <h4>${escHtml(tr("pest_result_title"))}</h4>
        <div class="response-text">${safeFormat(data.advice)}</div>
      </div>`;
  } catch (err) {
    resultEl.innerHTML = renderError(tr("err_server"));
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// UTILITY HELPERS
// ═══════════════════════════════════════════════════════════════════════════════
function renderLoading(msg) {
  return `<div class="loading"><div class="spinner"></div>${escHtml(msg || "Loading...")}</div>`;
}
function renderError(msg) {
  return `<div class="error-box">❌ ${escHtml(msg || "An error occurred.")}</div>`;
}
function escHtml(str) {
  if (typeof str !== "string") return String(str ?? "");
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
function formatDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr + "T00:00:00");
  return d.toLocaleDateString("en-IN", { weekday: "short", month: "short", day: "numeric" });
}

/**
 * safeFormat — safely convert plain AI text to readable HTML.
 * Escapes HTML entities first, then converts:
 *   - Blank lines     → paragraph breaks
 *   - Single newlines → <br>
 *   - **bold**        → <strong>
 *   - Leading "- "   → list items (wrapped in a single <ul>)
 * This is intentionally minimal — no markdown parser needed.
 */
function safeFormat(text) {
  if (!text || typeof text !== "string") return "";
  // 1. Escape HTML
  let s = escHtml(text.trim());
  // 2. Bold (**text**)
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // 3. Paragraphs (double newline)
  s = s.replace(/\n{2,}/g, "</p><p>");
  s = "<p>" + s + "</p>";
  // 4. Single newlines remaining
  s = s.replace(/\n/g, "<br>");
  // 5. Convert "- item" lines inside paragraphs into <ul><li> structures
  s = s.replace(/<p>((?:- .+?(?:<br>|$))+)<\/p>/g, (_, block) => {
    const items = block
      .replace(/<br>/g, "\n")
      .split("\n")
      .filter(l => l.trim().startsWith("- "))
      .map(l => `<li>${l.replace(/^-\s*/, "").trim()}</li>`)
      .join("");
    return items ? `<ul>${items}</ul>` : `<p>${block}</p>`;
  });
  return s;
}
