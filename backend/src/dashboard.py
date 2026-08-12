import sqlite3
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


# ================================================================
# CONFIGURATION
# ================================================================

DATABASE_PATH = Path(__file__).parent / "health_access.db"

HOST = "127.0.0.1"
PORT = 8080


# ================================================================
# ANALYTICS
# ================================================================

def get_call_statistics():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM call_analytics
        """
    )

    total_calls = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM call_analytics
        WHERE outcome = 'successful'
        """
    )

    successful_calls = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM call_analytics
        WHERE outcome = 'failed'
        """
    )

    failed_calls = cursor.fetchone()[0]

    connection.close()

    return (
        total_calls,
        successful_calls,
        failed_calls,
    )


# ================================================================
# ESCALATIONS
# ================================================================

def get_escalations():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            reference_id,
            reason,
            summary,
            urgency,
            language,
            preferred_followup,
            status,
            created_at
        FROM escalations
        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ================================================================
# DASHBOARD HTML
# ================================================================

def build_dashboard():

    (
        total_calls,
        successful_calls,
        failed_calls,
    ) = get_call_statistics()

    escalations = get_escalations()

    success_rate = 0

    if total_calls > 0:

        success_rate = round(
            (successful_calls / total_calls) * 100
        )

    cards = ""

    for item in escalations:

        reference_id = html.escape(
            str(item["reference_id"])
        )

        reason = html.escape(
            str(item["reason"])
        )

        summary = html.escape(
            str(item["summary"])
        )

        urgency = html.escape(
            str(item["urgency"])
        )

        language = html.escape(
            str(item["language"] or "Unknown")
        )

        followup = html.escape(
            str(item["preferred_followup"] or "Unknown")
        )

        status = html.escape(
            str(item["status"])
        )

        created_at = html.escape(
            str(item["created_at"])
        )

        reason_display = reason.replace(
            "_",
            " "
        ).title()

        cards += f"""
        <div class="request">

            <div class="request-top">

                <div>

                    <div class="reference">
                        {reference_id}
                    </div>

                    <div class="reason">
                        {reason_display}
                    </div>

                </div>

                <div class="badges">

                    <span class="badge urgency-{urgency}">
                        {urgency.upper()}
                    </span>

                    <span class="badge status">
                        {status.upper()}
                    </span>

                </div>

            </div>

            <div class="summary">
                {summary}
            </div>

            <div class="details">

                <div>
                    <small>Language</small>
                    <strong>{language}</strong>
                </div>

                <div>
                    <small>Follow-up</small>
                    <strong>{followup}</strong>
                </div>

                <div>
                    <small>Created</small>
                    <strong>{created_at}</strong>
                </div>

            </div>

        </div>
        """

    if not cards:

        cards = """
        <div class="no-requests">
            No human escalation requests yet.
        </div>
        """

    return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    http-equiv="refresh"
    content="5"
>

<title>
    Health Access Analytics
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{

    margin: 0;

    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    background: #f5f7fb;

    color: #172033;

}}

.container {{

    max-width: 1200px;

    margin: auto;

    padding: 40px 24px 60px;

}}

.header {{

    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 32px;

}}

.title h1 {{

    margin: 0;

    font-size: 28px;

}}

.title p {{

    margin: 6px 0 0;

    color: #687386;

}}

.refresh {{

    color: #687386;

    font-size: 13px;

}}

.stats {{

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 16px;

    margin-bottom: 36px;

}}

.stat {{

    background: white;

    border: 1px solid #e4e8ef;

    border-radius: 16px;

    padding: 24px;

}}

.stat-label {{

    color: #687386;

    font-size: 13px;

    margin-bottom: 10px;

}}

.stat-number {{

    font-size: 34px;

    font-weight: 700;

}}

.section-title {{

    margin-bottom: 16px;

}}

.section-title h2 {{

    margin: 0;

    font-size: 20px;

}}

.requests {{

    display: flex;

    flex-direction: column;

    gap: 16px;

}}

.request {{

    background: white;

    border: 1px solid #e4e8ef;

    border-radius: 16px;

    padding: 24px;

}}

.request-top {{

    display: flex;

    justify-content: space-between;

    gap: 20px;

}}

.reference {{

    font-weight: 700;

    font-size: 17px;

}}

.reason {{

    color: #687386;

    margin-top: 5px;

}}

.badges {{

    display: flex;

    gap: 8px;

}}

.badge {{

    padding: 6px 10px;

    border-radius: 20px;

    font-size: 11px;

    font-weight: 700;

}}

.status {{

    background: #e7f5ea;

    color: #28733d;

}}

.urgency-low {{

    background: #eef1f5;

    color: #586474;

}}

.urgency-medium {{

    background: #fff3cf;

    color: #826300;

}}

.urgency-high {{

    background: #ffe5d6;

    color: #a64a15;

}}

.urgency-emergency {{

    background: #ffe0e0;

    color: #a51d1d;

}}

.summary {{

    margin-top: 20px;

    padding: 16px;

    background: #f6f7f9;

    border-radius: 12px;

    line-height: 1.6;

}}

.details {{

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 20px;

    margin-top: 18px;

}}

.details div {{

    display: flex;

    flex-direction: column;

    gap: 4px;

}}

.details small {{

    color: #8993a4;

}}

.details strong {{

    font-size: 14px;

}}

.no-requests {{

    background: white;

    border: 1px solid #e4e8ef;

    border-radius: 16px;

    padding: 40px;

    color: #687386;

}}

@media(max-width: 800px) {{

    .stats {{

        grid-template-columns:
            repeat(2, 1fr);

    }}

    .request-top {{

        flex-direction: column;

    }}

    .details {{

        grid-template-columns: 1fr;

    }}

}}

@media(max-width: 500px) {{

    .stats {{

        grid-template-columns: 1fr;

    }}

}}

</style>

</head>

<body>

<div class="container">

    <div class="header">

        <div class="title">

            <h1>
                Health Access Analytics
            </h1>

            <p>
                Call performance and human support
            </p>

        </div>

        <div class="refresh">
            Auto-refresh: 5 seconds
        </div>

    </div>


    <div class="stats">

        <div class="stat">

            <div class="stat-label">
                Total Calls
            </div>

            <div class="stat-number">
                {total_calls}
            </div>

        </div>


        <div class="stat">

            <div class="stat-label">
                Successful Calls
            </div>

            <div class="stat-number">
                {successful_calls}
            </div>

        </div>


        <div class="stat">

            <div class="stat-label">
                Failed Calls
            </div>

            <div class="stat-number">
                {failed_calls}
            </div>

        </div>


        <div class="stat">

            <div class="stat-label">
                Success Rate
            </div>

            <div class="stat-number">
                {success_rate}%
            </div>

        </div>

    </div>


    <div class="section-title">

        <h2>
            Human Support Requests
        </h2>

    </div>


    <div class="requests">

        {cards}

    </div>

</div>

</body>

</html>
"""


# ================================================================
# HTTP SERVER
# ================================================================

class DashboardHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/" or self.path.startswith("/?"):

            page = build_dashboard()

            data = page.encode(
                "utf-8"
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(data))
            )

            self.end_headers()

            self.wfile.write(data)

        else:

            self.send_response(404)

            self.end_headers()

    def log_message(self, format, *args):

        print(
            f"[Dashboard] {format % args}"
        )


# ================================================================
# START
# ================================================================

def main():

    print()
    print("=" * 60)
    print("Health Access Analytics Dashboard")
    print("=" * 60)
    print()
    print(
        f"Dashboard: http://{HOST}:{PORT}"
    )
    print()
    print(
        "Auto-refresh: 5 seconds"
    )
    print()
    print(
        "Press CTRL+C to stop."
    )
    print()

    server = HTTPServer(
        (HOST, PORT),
        DashboardHandler,
    )

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print()
        print("Dashboard stopped.")

    finally:

        server.server_close()


if __name__ == "__main__":
    main()
