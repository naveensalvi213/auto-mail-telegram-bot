from database.db import DatabaseManager

MAIL_SET_1 = [
    ("salvinaveen478@gmail.com", "hwbajpgwoexmxdjl"),
    ("salvinaveen11@gmail.com", "ofbmrbewgapjdjib"),
    ("salvinaveen53@gmail.com", "pxpdhlvyofkfjvtb"),
    ("naveensalvi122@gmail.com", "pfifzeejscjhxpyz"),
    ("narusalvi142@gmail.com", "diwnuipjmvrbplav"),
    ("neoscale005@gmail.com", "tlfqvififghvhwwd"),
    ("editsneo63@gmail.com", "wrracphhzummbquc"),
    ("neoscale459@gmail.com", "mssvxzanbyhqiuqg"),
    ("nuclearstudiohq@gmail.com", "cxuoofxqpebkjlcx"),
    ("nuclearedithq@gmail.com", "xehwlbobdnmuwppw")
]

MAIL_SET_2 = [
    ("neocollabe@gmail.com", "alwtgliymjsdzozc"),
    ("neostudion@gmail.com", "cjptbckgnnbhhzlp"),
    ("neoscale004@gmail.com", "puoesuzjnyusfgte"),
    ("neoscale001@gmail.com", "lbdcbwihdjkzwvpj"),
    ("naveen.salvi02@gmail.com", "vrwxbwvzawkpevhw"),
    ("naveensalvi0202@gmail.com", "efpqhcjtfcbzsthr"),
    ("alexwilliams0621@gmail.com", "diuqjekvxbecnxkz"),
    ("tylerbrooks0621@gmail.com", "mutgzodvsqiyfdvc"),
    ("editsalex99@gmail.com", "qvsgetegxzaehgjb"),
    ("xeno.smma@gmail.com", "kmwoximojpnfdfao")
]

TEMPLATE_SET_1 = [
    (
        "We’d like to build this for [Channel Name], free",
        "Hey [Channel Name],\n\nWe came across your channel and noticed a few things that could potentially be improved with AI automation.\n\nWe’re currently building our portfolio, so we’d love to build an automation system for your channel completely free.\n\nThere’s no payment or commitment. If you’re happy with the result, we’d simply ask for an honest review that we can feature in our portfolio.\n\nWould you be open to it?"
    ),
    (
        "Quick idea for [Channel Name] workflow",
        "Hi [Channel Name],\n\nLove the content you're publishing. I noticed your team might be spending significant time on video processing and content repurposing.\n\nWe specialize in building custom AI workflows that handle video clipping, metadata generation, and multi-platform publishing automatically.\n\nCould we set up a free prototype custom-built for [Channel Name]? No catch at all—we just want a case study for our new automation platform.\n\nLet me know if you're interested!"
    ),
    (
        "Free AI automation build for [Channel Name]",
        "Hey [Channel Name] team,\n\nI hope you're having a great week!\n\nOur team builds custom AI systems for content creators that save 15+ hours a week on video editing, scripting assistance, and fan engagement.\n\nWe're selecting 5 high-quality channels to build free custom automations for this month in exchange for feedback.\n\nWould [Channel Name] be interested in being one of them?"
    ),
    (
        "Automating repetitive tasks for [Channel Name]?",
        "Hi [Channel Name],\n\nQuick question: Are you currently using any AI tools to streamline your production and distribution workflow?\n\nWe've designed an automated pipeline specifically tailored for creators like [Channel Name] to cut production overhead by 60%.\n\nWe'd be happy to build and implement a custom automation module for [Channel Name] free of charge.\n\nWorth a 5-minute chat?"
    ),
    (
        "Custom workflow upgrade for [Channel Name]",
        "Hey [Channel Name],\n\nHuge fan of your channel! We noticed opportunities to automate your thumbnail testing, title generation, and comment triage using LLM workflows.\n\nWe'd love to build a completely free custom workflow for [Channel Name] to demonstrate how much time you can save.\n\nZero cost, zero obligation. Interested in seeing what we can create for you?"
    ),
    (
        "Collaboration proposal for [Channel Name]",
        "Hello [Channel Name],\n\nWe are an AI automation agency expanding into media channel optimizations.\n\nWe are offering to build a tailored AI pipeline for [Channel Name]—from topic research to automated post-production asset generation—100% free.\n\nAll we ask in return is a short testimonial if it adds real value to your workflow.\n\nCan I send over a quick video explaining how it works?"
    ),
    (
        "15+ hours saved weekly for [Channel Name]",
        "Hey [Channel Name],\n\nWhat if your team could save 15+ hours every week on manual content ops?\n\nWe build custom AI automations for channels in your niche, helping automate research, editing workflows, and distribution.\n\nWe'd love to build a free custom tool for [Channel Name] as part of our client showcase.\n\nLet me know if you'd like to take a look!"
    ),
    (
        "Scaling [Channel Name] with custom AI tools",
        "Hi [Channel Name],\n\nWe help creators scale their content volume without increasing team size by deploying private AI automation agents.\n\nI'd love to set up a dedicated automation tool for [Channel Name] at zero cost to show you what's possible.\n\nWould you be open to exploring this?"
    ),
    (
        "Free AI content pipeline for [Channel Name]",
        "Hey [Channel Name],\n\nI came across your content and was really impressed by your quality and consistency!\n\nMy team builds automated AI pipelines that turn long-form videos into shorts, social posts, and newsletter digests automatically.\n\nWe'd love to set up a free trial build for [Channel Name]. No credit card or commitment required.\n\nWould you be open to a quick preview?"
    ),
    (
        "AI system tailored for [Channel Name]",
        "Hi [Channel Name] team,\n\nWe are offering free custom AI workflow builds for select top channels this month.\n\nWe can build automated script outline generators, trend alerts, or distribution bots specifically for [Channel Name].\n\nIf this sounds interesting, reply to this email and I'll share a quick concept mockup!"
    )
]

TEMPLATE_SET_2 = [
    (
        "AI agent for [Channel Name]",
        "Hey [Channel Name],\n\nWe built an AI agent that automatically converts your YouTube videos into viral Shorts, X threads, and LinkedIn posts in under 2 minutes.\n\nWe want to set this up for [Channel Name] for free so you can double your reach without extra work.\n\nWould you like me to send over a sample of what it creates for your latest video?"
    ),
    (
        "Automated sponsor & deal pipeline for [Channel Name]",
        "Hi [Channel Name],\n\nManaging brand inquiries and sponsor negotiations can take up a ton of time.\n\nWe built an AI inbox assistant that filters incoming brand deals, qualifies budgets, and drafts responses for creators automatically.\n\nWe'd love to deploy a free demo version for [Channel Name].\n\nOpen to taking a look?"
    ),
    (
        "AI video editing workflow for [Channel Name]",
        "Hey [Channel Name],\n\nOur team developed an AI-assisted video editing workflow that cuts rough editing time by 70%.\n\nWe're offering to process one of [Channel Name]'s upcoming videos for free to show you how seamless it is.\n\nWould you be open to trying it on your next upload?"
    ),
    (
        "Double [Channel Name]'s upload frequency with AI",
        "Hi [Channel Name],\n\nWhat's the main bottleneck keeping [Channel Name] from posting twice as often?\n\nWhether it's scripting, editing, or thumbnail creation, we build custom AI agents that eliminate creator bottlenecks.\n\nWe'd love to build a custom solution for your biggest bottleneck completely free.\n\nLet me know if you're open to a quick chat!"
    ),
    (
        "Automated thumbnail & title optimizer for [Channel Name]",
        "Hey [Channel Name] team,\n\nCTR is everything. We built an AI system that generates and tests 10+ high-CTR title and thumbnail concepts for every video.\n\nWe'd like to run a free optimization batch for [Channel Name]'s next video.\n\nCan I send you 3 free title/thumbnail concepts for your next topic?"
    ),
    (
        "AI audience growth engine for [Channel Name]",
        "Hi [Channel Name],\n\nWe created an automated AI growth engine that analyzes high-performing video trends in your niche every morning.\n\nIt sends customized topic ideas directly to your inbox tailored specifically for [Channel Name].\n\nWe can turn this on for [Channel Name] for 30 days free of charge.\n\nWant to see the first batch of trend reports tomorrow morning?"
    ),
    (
        "Repurposing [Channel Name]'s content automatically",
        "Hey [Channel Name],\n\nAre you leaving views on the table by not repurposing your videos across TikTok, IG Reels, and Shorts?\n\nOur AI automation pipeline handles clipping, captioning, and distribution for [Channel Name] on autopilot.\n\nWe'd love to process 3 of your existing videos into short-form content for free.\n\nInterested?"
    ),
    (
        "Streamline [Channel Name]'s production with AI",
        "Hi [Channel Name],\n\nWe help creator teams streamline their production stacks using custom Python & AI automations.\n\nWe're offering a free 1-on-1 workflow audit and custom bot build for [Channel Name].\n\nIf you're interested, reply with \"YES\" and I'll send over the details."
    ),
    (
        "Custom AI research assistant for [Channel Name]",
        "Hey [Channel Name],\n\nDeep research takes hours. We built an AI research bot that pulls verified facts, papers, and quotes for video scripts in seconds.\n\nWe'd love to set up a custom instance of this bot tailored for [Channel Name]'s niche—100% free.\n\nWould you be open to testing it out?"
    ),
    (
        "Zero-cost AI automation build for [Channel Name]",
        "Hi [Channel Name],\n\nWe are launching a new AI workflow agency and building case studies with top creators.\n\nWe will design, code, and deploy a full custom AI automation for [Channel Name] with zero upfront or hidden fees.\n\nAll we ask is a review if you love it.\n\nCan we set up a quick 10-minute call this week?"
    )
]

def seed_initial_data(db_manager: DatabaseManager) -> None:
    """Populate database with pre-configured Mail Sets and Template Sets if not present."""
    db_manager.init_db()

    # Seed Mail Set 1
    existing_mail_sets = db_manager.get_all_mail_sets()
    if "Mail Set 1" not in existing_mail_sets:
        for email, passw in MAIL_SET_1:
            db_manager.add_mail_account("Mail Set 1", email, passw)

    # Seed Mail Set 2
    if "Mail Set 2" not in existing_mail_sets:
        for email, passw in MAIL_SET_2:
            db_manager.add_mail_account("Mail Set 2", email, passw)

    # Seed Template Set 1
    existing_template_sets = db_manager.get_all_template_sets()
    if "Template Set 1" not in existing_template_sets:
        for subject, body in TEMPLATE_SET_1:
            db_manager.add_template("Template Set 1", subject, body)

    # Seed Template Set 2
    if "Template Set 2" not in existing_template_sets:
        for subject, body in TEMPLATE_SET_2:
            db_manager.add_template("Template Set 2", subject, body)
