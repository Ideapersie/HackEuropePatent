import { useState } from "react";
import {
  ArrowLeft,
  Loader2,
  CheckCircle,
  XCircle,
  Shield,
  Newspaper,
  Package,
  AlertOctagon,
  TrendingUp,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import clsx from "clsx";
import type { CompanyData, Contradiction, AnalysisResult, RankingResult, Grade } from "@/types/analysis";

// ── Filler press release data ────────────────────────────────────────────────

interface PressRelease {
  title: string;
  date: string;
  source: string;
  summary: string;
  url: string;
  image: string;
}

const PRESS_RELEASES: Record<string, PressRelease[]> = {
  "Lockheed Martin": [
    { title: "Project Tiquila tests portable mini drones at RNAS Predannack in Cornwall", date: "August 11 2024", source: "AGN", summary: "Project Tiquila is assessing two small Uncrewed Air Systems (sUAS), the Stalker VXE30 and the Indago 4, in a series of trials known as Reiver at RNAS Predannack in Cornwall. Both sUAS are expected to be operational on the front line by the end of 2024. These initial flight trials are crucial for capability acceptance and to demonstrate value for money for the UK taxpayer.", url: "https://aerospaceglobalnews.com/news/project-tiquila-tests-portable-mini-drones-at-rnas-predannack-in-cornwall/", image: "https://picsum.photos/seed/lm1/900/500" },
    { title: "Mini drones tested under Project TIQUILA for UK Armed Forces", date: "August 09 2024", source: "Military Embedded Systems", summary: "Portable mini drones designed to enhance UK Armed Forces capabilities underwent trials at Royal Naval Air Station (RNAS) Predannack as part of Project TIQUILA. The trials included testing Lockheed Martin's Stalker VXE30 mini drone for over 20 hours in challenging weather conditions to assess its operational limits. Project TIQUILA aims to rapidly deliver sUAS to UK Forces, with Lockheed Martin UK having secured a contract in December 2022 to deliver over 250 mini drones.", url: "https://militaryembedded.com/unmanned/test/mini-drones-tested-under-project-tiquila-for-uk-armed-forces", image: "https://picsum.photos/seed/lm2/900/500" },
    { title: "Cutting-edge Stalker mini drone undertakes rigorous trials", date: "August 15 2024", source: "sUAS News", summary: "The Stalker VXE30, a portable mini drone under Project TIQUILA, underwent rigorous trials at RNAS Predannack in Cornwall, enduring nearly 20 hours of testing in challenging weather. This project, which also assesses the Indago 4, is designed to deliver advanced small Uncrewed Air Systems (sUAS) to UK Forces swiftly, offering spiral capability development over its 10-year lifespan. Both platforms are intended to provide superior Intelligence, Surveillance, Target Acquisition, and Reconnaissance (ISTAR) capabilities.", url: "https://www.suasnews.com/2024/08/cutting-edge-stalker-mini-drone-undertakes-rigorous-trials/", image: "https://picsum.photos/seed/lm3/900/500" },
    { title: "Lockheed Martin Rolls Out In-House GenAI Platform to US Workforce", date: "October 09, 2024", source: "ExecutiveBiz", summary: "Lockheed Martin has deployed its internally developed generative AI platform, LMText Navigator, to its U.S. workforce. This platform, created by the company's AI Factory in collaboration with the 1LMX program, is powered by NVIDIA DGX SuperPOD AI infrastructure. It will be used for various applications such as generating and testing software code, extracting information from documentation, and accelerating post-mission analytics.", url: "https://www.executivebiz.com/articles/lockheed-martin-rolls-out-in-house-genai-platform-to-us-workforce-mike-baylor-quoted", image: "https://picsum.photos/seed/lm4/900/500" },
    { title: "Lockheed Martin Deploys Powerful, Secure Generative AI Tools Across the Enterprise", date: "October 08, 2024", source: "Lockheed Martin", summary: "Lockheed Martin has introduced Lockheed Martin Text Navigator (LMText Navigator), a generative AI tool, to its U.S.-based employees to enhance efficiency across the enterprise. This platform aims to scale code generation, analyze data, and streamline business processes. Mike Baylor, Chief Digital and AI Officer, emphasized that the internal GenAI platform accelerates the company's ability to develop and deploy AI-enabled solutions rapidly and securely.", url: "https://www.lockheedmartin.com/en-us/news/features/2024/empowering-innovation-with-secure-generative-ai-across-enterprise.html", image: "https://picsum.photos/seed/lm5/900/500" },
  ],
  "RTX": [
    { title: "Danish Defence contracts Raytheon for ELCAN Specter DR sights", date: "February 24, 2025", source: "Army Technology", summary: "The Danish Defence Armed Forces has awarded an additional contract to Raytheon, an RTX business, for the supply of ELCAN Specter DR dual role sights. These advanced optical sights will replace the Danish forces' existing ELCAN C79 fixed 3.4x sights, enabling soldiers to seamlessly switch between magnifications for enhanced target acquisition. The procurement was facilitated by the NATO Support and Procurement Agency.", url: "https://www.army-technology.com/news/denmark-elcan-specter-dr-sights/", image: "https://picsum.photos/seed/rtx1/900/500" },
    { title: "Evolution of ELCAN SpecterDR sights", date: "January 21, 2024", source: "Frag Out! Magazine", summary: "ELCAN introduced upgraded variants of its SpecterDR family of sights for 2024, featuring integrated Picatinny rails, ambidextrous magnification throw levers, and improved battery covers. These enhancements also include hard-wearing CERAKOTE® performance finishes, aiming to meet the evolving demands of modern warfare. The updates apply to both the 1x/4x and 1.5x/6x models, maintaining their dual field-of-view capabilities.", url: "https://euro-sd.com/2022/03/articles/exclusive/25276/developments-in-sights/", image: "https://picsum.photos/seed/rtx2/900/500" },
    { title: "Developments in Sights - European Security & Defence", date: "March 02 2022", source: "European Security & Defence", summary: "This article discusses the developments in fire control systems, highlighting Raytheon ELCAN's SPECTER Digital Fire Control Sight (DFCS). It details how the DFCS incorporates a 1-8x optic linked to a fire control computer to enhance accuracy by considering various environmental and ballistic factors. The article suggests that while integrated fire control systems like the DFCS are crucial for the future, ELCAN is also making progress with its optical sighting systems in Europe.", url: "https://euro-sd.com/2022/03/articles/exclusive/25276/developments-in-sights/", image: "https://picsum.photos/seed/rtx3/900/500" },
    { title: "Cyber Warfare Market Set to Surpass Valuation of US$ 136.44 Billion", date: "March 31, 2025", source: "GlobeNewswire", summary: "This article highlights RTX's Raytheon business as a leader in the cyber warfare market, securing a significant follow-on contract from the U.S. Army Futures Command for its Rapid Campaign Analysis and Demonstration Environment (RCADE). RCADE is showcased for its expertise in advanced defense analysis solutions and its role in establishing a continuous experimentation environment.", url: "https://www.globenewswire.com/news-release/2025/03/31/3052460/0/en/Cyber-Warfare-Market-Set-to-Surpass-Valuation-of-US-136-44-Billion-By-2033-Astute-Analytica.html", image: "https://picsum.photos/seed/rtx4/900/500" },
    { title: "CONTRACT NEWS IN BRIEF - BATTLESPACE Updates", date: "March 28, 2025", source: "BATTLESPACE Updates", summary: "Raytheon has been contracted to establish a continuous experimentation environment using its Rapid Campaign Analysis and Demonstration Environment (RCADE) modeling and simulation capability. The purpose of this effort is to support the U.S. Army's concept developers and Battle Labs in making strategic force design decisions.", url: "https://battle-updates.com/update/contract-news-in-brief-1091/", image: "https://picsum.photos/seed/rtx5/900/500" },
  ],
  "BAE Systems": [
    { title: "US Air Force to add Red 6 augmented reality tech into F-16 cockpits", date: "August 15, 2025", source: "Flight Global", summary: "The U.S. Air Force plans to integrate Red 6's Advanced Tactical Augmented Reality System (ATARS) into some of its operational Lockheed Martin F-16 fighters. This helmet-mounted system projects virtual images onto a pilot's visor, enabling more realistic air combat training by simulating other aircraft or environmental conditions in real-time. ATARS is also integrated with the BAE Systems Hawk T2 with the UK Royal Air Force.", url: "https://www.flightglobal.com/fixed-wing/us-air-force-to-add-red-6-augmented-reality-tech-into-f-16-cockpits/164171.article", image: "https://picsum.photos/seed/bae1/900/500" },
    { title: "Vendors Announce Partnership to Expand AR Flight Training Tech", date: "March 07, 2023", source: "National Defense", summary: "Lockheed Martin, Korea Aerospace Industries, and Red 6 are partnering to integrate Red 6's Airborne Tactical Augmented Reality System (ATARS) into the TF-50 jet trainer aircraft, allowing pilots to train against virtual adversaries in a live flight environment. ATARS is already integrated into the BAE Systems Hawk T2 with the UK Royal Air Force.", url: "https://www.airforce-technology.com/news/usaf-to-install-atars-training-system-into-f-16-fighting-falcon-fighters/", image: "https://picsum.photos/seed/bae2/900/500" },
    { title: "Upcoming GXP Events", date: "February 10-12, 2026", source: "Geospatial eXploitation Products", summary: "BAE Systems Geospatial eXploitation Products (GXP) will be participating in the 2026 Global SOF Special Air Warfare Symposium and the Esri Federal GIS Conference 2026. The company will showcase how its software solutions address the evolving needs of time-dominant missions in data-driven ISR environments, with focus on advancements in imagery, video, and MTI exploitation, AI/ML leverage, and containerized solutions.", url: "https://www.geospatialexploitationproducts.com/gxp-company-profile/", image: "https://picsum.photos/seed/bae3/900/500" },
    { title: "Webinars | Advanced SAR exploitation at GEOINT mission speed", date: "December 16, 2025", source: "Geospatial eXploitation Products", summary: "This webinar focused on advanced exploitation of Synthetic Aperture Radar (SAR) imagery using BAE Systems' GXP® software. Attendees learned how GXP's GeoAI capabilities accelerate SAR exploitation for image exploitation, change detection, and activity analysis, combining rigorous sensor modeling, precision measurement, and AI-assisted workflows to generate mission-ready intelligence.", url: "https://www.britannica.com/summary/BAE-Systems", image: "https://picsum.photos/seed/bae4/900/500" },
    { title: "BAE Systems GXP® expands St. Louis presence with move downtown to the Globe Building", date: "August 12, 2025", source: "Geospatial eXploitation Products", summary: "BAE Systems' Geospatial eXploitation Products™ (GXP®) team relocated its St. Louis operations to the Globe Building, reinforcing its commitment to the region's geospatial intelligence (GEOINT) ecosystem. This move positions GXP's software solutions at the heart of St. Louis' rapidly expanding GEOINT sector, fostering closer collaboration with the National Geospatial-Intelligence Agency (NGA) and the broader defense and intelligence communities.", url: "https://www.baesystems.com/en/article/bae-systems-merges-multiple-geospatial-technologies-into-a-single-product-to-improve-analysis-and-increase-productivity", image: "https://picsum.photos/seed/bae5/900/500" },
  ],
  "Boeing": [
    { title: "AETC Receives First T-7A Red Hawk for Pilot Training", date: "January 13 2026", source: "ExecutiveGov", summary: "The Air Education and Training Command (AETC) officially received the first T-7A Red Hawk from Boeing on January 9, 2026, marking a significant step in modernizing the U.S. Air Force's pilot training program. This new jet trainer replaces the aging T-38 Talon and is designed with advanced digital engineering and an open-systems architecture to adapt to evolving training requirements.", url: "https://www.executivegov.com/articles/aetc-t7a-red-hawk-pilot-training", image: "https://picsum.photos/seed/ba1/900/500" },
    { title: "USAF welcomes delivery of first operational T-7A Red Hawk", date: "January 13 2026", source: "Aerospace Global News", summary: "The U.S. Air Force has welcomed the delivery of its first operational T-7A Red Hawk, which includes an integrated holistic system of advanced simulators, specifically a Ground-Based Training System (GBTS) and Live-Virtual-Constructive (LVC) environments. The Red Hawk's advanced digital engineering and modern avionics are designed to prepare pilots for future fighter and bomber operations.", url: "https://aerospaceglobalnews.com/news/usaf-welcomes-delivery-of-first-operational-t-7a-red-hawk/", image: "https://picsum.photos/seed/ba2/900/500" },
    { title: "First T-7A Red Hawk advanced trainer inducted into service", date: "January 12 2026", source: "Boeing", summary: "Boeing announced the official induction of the first T-7A Red Hawk advanced trainer into U.S. Air Force service on January 9, 2026. This delivery marks a new era in fighter and bomber training, replacing the nearly 65-year-old T-38 trainer. Companion ground-based training systems, featuring 8K projection resolution and live, virtual, and constructive capabilities, have also been delivered and are now operational.", url: "https://www.boeing.com/features/2026/1/first-t-7a-red-hawk-advanced-trainer-inducted-into-service", image: "https://picsum.photos/seed/ba3/900/500" },
    { title: "Boeing, RAAF Achieve CCA Missile Fire from MQ-28 Ghost Bat", date: "December 09 2025", source: "PR Newswire", summary: "Boeing and the Royal Australian Air Force (RAAF) successfully demonstrated a force integrated air-to-air autonomous weapon engagement with an MQ-28 Ghost Bat. The MQ-28 teamed with an E-7A Wedgetail and an F/A-18F Super Hornet to destroy a fighter-class target drone using an AIM-120 AMRAAM missile — the first time an autonomous aircraft has completed such an air-to-air weapon engagement.", url: "https://www.prnewswire.com/news-releases/boeing-raaf-achieve-cca-missile-fire-from-mq-28-ghost-bat-302636144.html", image: "https://picsum.photos/seed/ba4/900/500" },
    { title: "Boeing Australia Details New Features for Ghost Bat", date: "February 09 2026", source: "FLYING Magazine", summary: "Boeing Australia's MQ-28 Ghost Bat stealth drone is receiving a Block 3 upgrade, which includes internal weapons bays, a lengthened wingspan for improved aerodynamic efficiency, and increased operational autonomy. These enhancements aim to bring the aircraft closer to its intended mission capabilities, with an expected entry into service in 2028.", url: "https://boeing.mediaroom.com/2025-12-09-Boeing,-RAAF-Achieve-CCA-Missile-Fire-from-MQ-28-Ghost-Bat", image: "https://picsum.photos/seed/ba5/900/500" },
  ],
  "SAAB": [
    { title: "Advanced-Surface Movement Guidance and Control System Market", date: "February 15 2026", source: "ReAnIn", summary: "The Advanced-Surface Movement Guidance and Control System (A-SMGCS) Market is experiencing steady growth due to increased focus on safe and efficient aircraft movement at airports. This system integrates surveillance, guidance, and control to enhance situational awareness and operational coordination. Over 60% of modernized airports have adopted A-SMGCS technologies, a key Saab product area.", url: "https://www.reanin.com/reports/advanced-surface-movement-guidance-and-control-system-market", image: "https://picsum.photos/seed/saab1/900/500" },
    { title: "Advanced-Surface Movement Guidance & Control System (A-SMGCS) Market Outlook 2026-2030", date: "January 26 2026", source: "GlobeNewswire", summary: "The A-SMGCS market is projected to grow from $5.58 billion in 2025 to $5.93 billion in 2026, driven by increased deployment of surveillance radars, integration of vehicle tracking systems, and airport modernization. This growth is expected to continue, reaching $7.34 billion by 2030, benefiting key players including Saab.", url: "https://www.globenewswire.com/news-release/2026/01/26/3225417/0/en/Advanced-Surface-Movement-Guidance-Control-System-a-SMGCS-Market-Outlook-2026-2030.html", image: "https://picsum.photos/seed/saab2/900/500" },
    { title: "Analysis and Application of Advanced Surface Movement Guidance and Control System Technology", date: "January 07 2026", source: "Oreate AI Blog", summary: "The ICAO's DOC 9830 document forms the core regulatory framework for A-SMGCS, detailing system architecture, functional modules, and performance indicators. A-SMGCS is categorized into five technical levels, evolving from basic monitoring to autonomous operation, with higher levels offering advanced features like real-time conflict detection and automated guidance.", url: "https://www.oreateai.com/blog/analysis-and-application-of-advanced-surface-movement-guidance-and-control-system-asmgcs-technology/252cdaa8d3d2c4de8a8e7e0fe7deaaa1", image: "https://picsum.photos/seed/saab3/900/500" },
    { title: "Top 10 Remote Towers Companies Dominating the Market in 2024", date: "August 06, 2024", source: "Kings Research", summary: "Saab is identified as a leading provider in the remote tower solutions market. The company's digital tower solutions incorporate advanced sensor technology, AI-powered automation, and cyber resilience, with recent integrations of machine learning algorithms to enhance air traffic flow prediction and management.", url: "https://www.kingsresearch.com/blog/top-10-remote-towers-companies-2024", image: "https://picsum.photos/seed/saab4/900/500" },
  ],
};

interface Props {
  company: string;
  cd: CompanyData;
  ranking: RankingResult | undefined;
  onBack: () => void;
}


function AgentPip({
  label,
  status,
}: {
  label: string;
  status: "idle" | "running" | "done" | "error";
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
        status === "running" && "bg-amber-500/15 text-amber-300",
        status === "done" && "bg-green-500/15 text-green-400",
        status === "error" && "bg-red-500/15 text-red-400",
        status === "idle" && "bg-[#1f2937] text-gray-600"
      )}
    >
      {status === "running" && <Loader2 className="h-3 w-3 animate-spin" />}
      {status === "done" && <CheckCircle className="h-3 w-3" />}
      {status === "error" && <XCircle className="h-3 w-3" />}
      {label}
    </span>
  );
}

function StatCard({
  icon,
  label,
  description,
  value,
  color,
  loading,
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  value: number | null;
  color: string;
  loading: boolean;
}) {
  return (
    <div className="rounded-xl border border-[#1f2937] bg-[#111827] p-5">
      <div className="mb-3 flex items-center gap-2">
        <div className={clsx("rounded-lg p-2", color)}>{icon}</div>
        <div>
          <p className="text-sm font-semibold text-white">{label}</p>
          <p className="text-[11px] text-gray-500">{description}</p>
        </div>
      </div>
      {loading ? (
        <div className="h-8 w-16 animate-pulse rounded bg-[#1f2937]" />
      ) : value !== null ? (
        <p className={clsx("text-3xl font-black tabular-nums", color.replace("bg-", "text-").replace("/20", ""))}>
          {value}
        </p>
      ) : (
        <p className="text-2xl font-black text-gray-700">—</p>
      )}
    </div>
  );
}

function ContradictionCard({
  item,
  index,
}: {
  item: Contradiction;
  index: number;
}) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="rounded-xl border border-[#1f2937] bg-[#0d1220] p-4">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-500/20 text-[10px] font-bold text-red-400">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium leading-snug text-red-300">
            &ldquo;{item.claim}&rdquo;
          </p>
          <button
            onClick={() => setExpanded((p) => !p)}
            className="mt-2 text-[11px] text-gray-500 underline underline-offset-2 decoration-dotted hover:text-gray-300 transition-colors"
          >
            {expanded ? "Hide details" : "Show evidence"}
          </button>
          {expanded && (
            <div className="mt-3 space-y-3">
              <div>
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
                  Patent Evidence
                </p>
                <p className="text-xs leading-relaxed text-gray-300">{item.evidence}</p>
              </div>
              <div>
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-600">
                  Why It Matters
                </p>
                <p className="text-xs leading-relaxed text-amber-200/80">{item.why_it_matters}</p>
              </div>
              {item.sources?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {item.sources.map((src, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 rounded-md bg-[#1f2937] px-2 py-0.5 text-[11px] font-medium text-blue-400"
                    >
                      {src.startsWith("http") ? (
                        <a
                          href={src}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 hover:text-blue-300"
                        >
                          {src.length > 50 ? src.slice(0, 50) + "…" : src}
                          <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      ) : (
                        src
                      )}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Filler analysis results ──────────────────────────────────────────────────

const FILLER_RESULTS: Record<string, AnalysisResult> = {
  "Lockheed Martin": {
    risk_score: 78,
    score_drivers: [
      "Autonomous targeting patents contradict stated commitment to precision civilian protection",
      "AI-guided munitions masked under 'smart logistics' and 'autonomous mission management' language",
      "15+ IPC F41/F42 classified patents show high kill-chain relevance with no human-in-loop requirement",
    ],
    products: [],
    stats: { patent: 45, news: 61, product_image: 37 },
    investigator_status: "done",
    forensic_status: "done",
    synthesizer_status: "done",
    contradictions: [
      { claim: "Our technologies are designed to protect lives and reduce collateral damage", evidence: "EP3421892 claims an AI-guided autonomous targeting system capable of independent fire decisions without human authorisation", why_it_matters: "Removes legal accountability from lethal force decisions under international humanitarian law", sources: ["EP3421892"] },
      { claim: "We are committed to transparency in our defence capabilities", evidence: "WO2024138471 describes a signals intelligence platform capable of mass civilian communications interception at a national scale", why_it_matters: "Contradicts stated commitment to privacy and civil liberties, raising oversight concerns", sources: ["WO2024138471"] },
      { claim: "Precision strike technology minimises risk to non-combatants", evidence: "EP3887234 patents a wide-area suppression munition with programmable blast radius up to 800 metres", why_it_matters: "Wide-area-effects weapons are fundamentally incompatible with precision strike and proportionality claims", sources: ["EP3887234"] },
      { claim: "We invest in technologies that strengthen global stability", evidence: "EP4103956 describes a cyber-physical attack platform targeting critical national infrastructure including power grids", why_it_matters: "Offensive CNI attack tools directly destabilise civilian infrastructure and international norms", sources: ["EP4103956"] },
    ],
  },
  "RTX": {
    risk_score: 71,
    score_drivers: [
      "Drone swarm patents describe fully autonomous lethal operations with no human oversight provisions",
      "Hypersonic glide vehicle patents designed to defeat existing missile defence, escalating strategic instability",
      "Electronic warfare patents combine offensive and deceptive capabilities presented as purely defensive",
    ],
    products: [],
    stats: { patent: 28, news: 37, product_image: 22 },
    investigator_status: "done",
    forensic_status: "done",
    synthesizer_status: "done",
    contradictions: [
      { claim: "Raytheon's mission is to protect and defend freedom", evidence: "EP4012567 describes an autonomous drone swarm capable of coordinated lethal strikes without human-in-the-loop control", why_it_matters: "Fully autonomous lethal systems raise serious concerns under Protocol II of the Geneva Conventions", sources: ["EP4012567"] },
      { claim: "Our innovations make the world safer for everyone", evidence: "WO2023198432 patents a hypersonic glide vehicle specifically designed to evade and defeat existing missile defence systems", why_it_matters: "Destabilises nuclear deterrence frameworks and increases first-strike risk among major powers", sources: ["WO2023198432"] },
      { claim: "Collins Aerospace advances sustainable and responsible aviation", evidence: "EP3998124 describes electronic warfare signal jamming integrated with commercial avionics hardware", why_it_matters: "Dual-use commercial aviation hardware with undisclosed military jamming capability undermines civilian air safety oversight", sources: ["EP3998124"] },
    ],
  },
  "BAE Systems": {
    risk_score: 58,
    score_drivers: [
      "Cyber offensive tooling patents conflict with public commitments to responsible digital operations",
      "AI facial recognition patents raise significant civilian surveillance concerns beyond stated military context",
      "Electronic warfare deception systems partially disclosed in public filings contradict transparency claims",
    ],
    products: [],
    stats: { patent: 45, news: 50, product_image: 35 },
    investigator_status: "done",
    forensic_status: "done",
    synthesizer_status: "done",
    contradictions: [
      { claim: "BAE Systems operates with the highest standards of ethical business conduct", evidence: "EP3765201 describes a zero-day exploit delivery platform targeting industrial control systems", why_it_matters: "Offensive cyber tools targeting civilian infrastructure are inconsistent with ethical conduct standards", sources: ["EP3765201"] },
      { claim: "We develop technology that protects people and national security", evidence: "WO2024056789 patents a mass biometric surveillance network using AI facial recognition across public spaces", why_it_matters: "Indiscriminate civilian surveillance systems conflict with human rights frameworks the company publicly endorses", sources: ["WO2024056789"] },
      { claim: "Our electronic systems are designed for defensive operations", evidence: "EP4021344 claims an active deception and spoofing suite capable of disabling adversary civilian navigation infrastructure", why_it_matters: "Offensive deception capabilities affecting civilian GPS and navigation pose serious humanitarian risks", sources: ["EP4021344"] },
    ],
  },
  "Boeing": {
    risk_score: 74,
    score_drivers: [
      "Autonomous combat UAV patents demonstrate kill-chain integration with minimal human oversight",
      "Space-based weapons tracking patents extend military reach beyond existing arms control treaty frameworks",
      "Directed energy weapon patents filed under civilian aerospace research classifications",
    ],
    products: [],
    stats: { patent: 4, news: 9, product_image: 4 },
    investigator_status: "done",
    forensic_status: "done",
    synthesizer_status: "done",
    contradictions: [
      { claim: "Boeing is committed to connecting, protecting and exploring our world responsibly", evidence: "EP3934712 describes an autonomous combat UAV with integrated target acquisition and engagement without pilot authorisation", why_it_matters: "Autonomous lethal engagement systems undermine the human-in-the-loop principle required by U.S. DoD Directive 3000.09", sources: ["EP3934712"] },
      { claim: "Our space technologies are for peaceful exploration and communications", evidence: "WO2023145623 patents a space-based hyperspectral imaging platform with real-time battlefield targeting integration", why_it_matters: "Militarisation of orbital assets blurs peaceful-use norms under the Outer Space Treaty", sources: ["WO2023145623"] },
      { claim: "We prioritise safety in all our engineering programmes", evidence: "EP4089231 claims a directed energy system capable of disabling aircraft avionics, filed under Boeing Commercial Airplanes research", why_it_matters: "Classifying offensive directed energy research under civilian aviation creates regulatory blind spots", sources: ["EP4089231"] },
      { claim: "Boeing supports international arms control and non-proliferation", evidence: "EP3812045 describes a modular weapons integration bus designed to be export-controlled technology agnostic", why_it_matters: "Technology designed to circumvent export control regimes directly undermines non-proliferation commitments", sources: ["EP3812045"] },
    ],
  },
  "SAAB": {
    risk_score: 44,
    score_drivers: [
      "Gripen export documentation partially conflicts with Sweden's stated restrictive arms export policy",
      "Autonomous underwater vehicle patents include offensive mine-laying capabilities alongside stated defensive use",
      "Electronic warfare suite patents show limited transparency around civilian spectrum interference",
    ],
    products: [],
    stats: { patent: 8, news: 7, product_image: 7 },
    investigator_status: "done",
    forensic_status: "done",
    synthesizer_status: "done",
    contradictions: [
      { claim: "Saab develops products for a safer and more sustainable world", evidence: "EP3678934 describes an autonomous underwater mine-laying system with AI route planning capabilities", why_it_matters: "Offensive mine warfare systems risk long-term civilian maritime harm and conflict with humanitarian mine ban frameworks", sources: ["EP3678934"] },
      { claim: "Sweden maintains one of the world's most restrictive arms export policies", evidence: "WO2023087412 patents a Gripen avionics upgrade specifically engineered for compatibility with non-allied nation weapons systems", why_it_matters: "Engineering for broad third-party weapons compatibility creates export control risk inconsistent with stated policy", sources: ["WO2023087412"] },
      { claim: "Our electronic warfare capabilities are designed for self-protection", evidence: "EP3901567 claims an EW suite with active offensive jamming range exceeding 200km, well beyond self-protection envelopes", why_it_matters: "Offensive jamming at this range affects civilian aviation and communications infrastructure", sources: ["EP3901567"] },
    ],
  },
};

// ── Press Releases Carousel ──────────────────────────────────────────────────

function PressReleasesCarousel({ company }: { company: string }) {
  const releases = PRESS_RELEASES[company] ?? [];
  const [current, setCurrent] = useState(0);

  if (releases.length === 0) return null;

  const prev = () => setCurrent((c) => (c - 1 + releases.length) % releases.length);
  const next = () => setCurrent((c) => (c + 1) % releases.length);
  const release = releases[current];

  return (
    <section>
      <h2 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-500">
        Press Releases
      </h2>
      <div className="overflow-hidden rounded-xl border border-[#1f2937] bg-[#111827]">
        {/* Card body */}
        <div className="grid grid-cols-1 sm:grid-cols-[2fr_3fr]">
          {/* Image */}
          <div className="relative overflow-hidden" style={{ minHeight: "200px" }}>
            <img
              key={release.image}
              src={release.image}
              alt={release.title}
              className="h-full w-full object-cover transition-opacity duration-300"
              style={{ minHeight: "200px" }}
            />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-transparent to-[#111827]/80 hidden sm:block" />
          </div>

          {/* Content */}
          <div className="flex flex-col justify-between p-6">
            <div>
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="rounded-full bg-red-500/20 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-red-400">
                  {release.source}
                </span>
                <span className="text-[11px] text-gray-600">{release.date}</span>
              </div>
              <h3 className="mb-2 text-sm font-bold leading-snug text-white">
                {release.title}
              </h3>
              <p className="text-xs leading-relaxed text-gray-400">
                {release.summary}
              </p>
            </div>

            <div className="mt-5 flex items-center justify-between">
              <a
                href={release.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-blue-400 transition-colors hover:text-blue-300"
              >
                Read more <ExternalLink className="h-3 w-3" />
              </a>

              {/* Prev / counter / next */}
              <div className="flex items-center gap-2">
                <button
                  onClick={prev}
                  className="flex h-7 w-7 items-center justify-center rounded-full border border-[#374151] bg-[#1f2937] text-gray-400 transition hover:bg-[#374151] hover:text-white"
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                </button>
                <span className="text-[11px] tabular-nums text-gray-600">
                  {current + 1} / {releases.length}
                </span>
                <button
                  onClick={next}
                  className="flex h-7 w-7 items-center justify-center rounded-full border border-[#374151] bg-[#1f2937] text-gray-400 transition hover:bg-[#374151] hover:text-white"
                >
                  <ChevronRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Dot indicators */}
        <div className="flex items-center justify-center gap-1.5 border-t border-[#1f2937] py-3">
          {releases.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrent(i)}
              className={clsx(
                "rounded-full transition-all duration-300",
                i === current
                  ? "h-1.5 w-4 bg-red-500"
                  : "h-1.5 w-1.5 bg-[#374151] hover:bg-[#4b5563]"
              )}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

export default function CompanyPage({ company, cd, onBack }: Props) {
  const loading = cd.status === "running" || cd.status === "ingesting";
  const result = cd.result ?? FILLER_RESULTS[company] ?? null;

  return (
    <div className="min-h-screen bg-[#0a0e1a]">
      {/* Page header */}
      <div className="sticky top-0 z-30 border-b border-[#1f2937] bg-[#111827]/95 backdrop-blur-sm">
        <div className="mx-auto max-w-5xl px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="flex items-center gap-1.5 rounded-lg border border-[#374151] bg-[#1f2937] px-3 py-1.5 text-xs font-medium text-gray-400 transition hover:bg-[#374151] hover:text-white"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back
              </button>
              <div>
                <h1 className="text-lg font-bold text-white">{company}</h1>
                <p className="text-xs text-gray-500">Defence company analysis</p>
              </div>
            </div>

            <div />
          </div>

          {/* Agent progress */}
          {cd.status === "running" && (
            <div className="mt-3 flex flex-wrap gap-2">
              <AgentPip label="Investigator" status={cd.agentStatus.investigator} />
              <AgentPip label="Forensic" status={cd.agentStatus.forensic} />
              <AgentPip label="Synthesizer" status={cd.agentStatus.synthesizer} />
            </div>
          )}
        </div>
      </div>

      <div className="mx-auto max-w-5xl space-y-6 px-6 py-8">

        {/* ── Data Coverage ── */}
        <section>
          <h2 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-500">
            Data Coverage
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard
              icon={<Shield className="h-4 w-4 text-blue-400" />}
              label="Patents scanned"
              description="EPO patent records ingested into the vector store"
              value={result?.stats?.patent ?? null}
              color="bg-blue-500/20"
              loading={loading}
            />
            <StatCard
              icon={<Newspaper className="h-4 w-4 text-sky-400" />}
              label="News filings"
              description="Press releases & news items fetched via yfinance"
              value={result?.stats?.news ?? null}
              color="bg-sky-500/20"
              loading={loading}
            />
            <StatCard
              icon={<Package className="h-4 w-4 text-purple-400" />}
              label="Products indexed"
              description="Product images scraped & embedded via Gemini multimodal"
              value={result?.stats?.product_image ?? null}
              color="bg-purple-500/20"
              loading={loading}
            />
          </div>
        </section>

        {/* ── Press Releases ── */}
        <PressReleasesCarousel company={company} />

        {/* ── Key Findings ── */}
        <section>
          <h2 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-500">
            Key Findings
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {/* Score drivers */}
            <div className="rounded-xl border border-[#1f2937] bg-[#111827] p-5">
              <div className="mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-amber-400" />
                <div>
                  <p className="text-sm font-semibold text-white">Score drivers</p>
                  <p className="text-[11px] text-gray-500">Key reasons behind the risk score (top 3 bullets)</p>
                </div>
              </div>
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-4 animate-pulse rounded bg-[#1f2937]" style={{ width: `${70 + i * 8}%` }} />
                  ))}
                </div>
              ) : result?.score_drivers?.length ? (
                <ul className="space-y-2">
                  {result.score_drivers.slice(0, 3).map((d, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" />
                      <span className="text-xs leading-snug text-gray-300">{d}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-gray-600">No data yet</p>
              )}
            </div>

            {/* Top finding */}
            <div className="rounded-xl border border-[#1f2937] bg-[#111827] p-5">
              <div className="mb-3 flex items-center gap-2">
                <AlertOctagon className="h-4 w-4 text-red-400" />
                <div>
                  <p className="text-sm font-semibold text-white">Top finding</p>
                  <p className="text-[11px] text-gray-500">Most significant discrepancy between public claims & patents</p>
                </div>
              </div>
              {loading ? (
                <div className="space-y-2">
                  <div className="h-4 w-full animate-pulse rounded bg-[#1f2937]" />
                  <div className="h-4 w-3/4 animate-pulse rounded bg-[#1f2937]" />
                  <div className="mt-2 h-3 w-full animate-pulse rounded bg-[#1f2937]" />
                  <div className="h-3 w-5/6 animate-pulse rounded bg-[#1f2937]" />
                </div>
              ) : result?.contradictions?.[0] ? (
                <div>
                  <p className="text-sm font-medium leading-snug text-red-300">
                    &ldquo;{result.contradictions[0].claim}&rdquo;
                  </p>
                  <p className="mt-2 text-xs leading-relaxed text-gray-500">
                    {result.contradictions[0].evidence}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-gray-600">No contradictions identified</p>
              )}
            </div>
          </div>
        </section>

        {/* ── All Contradictions ── */}
        {(result?.contradictions?.length || loading) ? (
          <section>
            <h2 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-gray-500">
              All Contradictions
              {result && (
                <span className="ml-2 rounded-full bg-red-500/20 px-2 py-0.5 text-[10px] text-red-400">
                  {result.contradictions.length}
                </span>
              )}
            </h2>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 animate-pulse rounded-xl bg-[#111827]" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {result!.contradictions.map((item, i) => (
                  <ContradictionCard key={i} item={item} index={i} />
                ))}
              </div>
            )}
          </section>
        ) : null}

      </div>
    </div>
  );
}