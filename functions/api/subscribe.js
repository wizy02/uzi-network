// functions/api/subscribe.js — Handle newsletter/pro signup form submissions
// Captures email and sends confirmation via Resend API

export async function onRequestPost(context) {
  const { request, env } = context;
  
  try {
    // Parse form body
    const body = await request.formData();
    const email = body.get("email")?.toString().trim().toLowerCase();
    const source = body.get("source")?.toString().trim() || "unknown";
    
    if (!email || !email.includes("@")) {
      return new Response(JSON.stringify({ error: "Invalid email" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Load Resend API key from service credentials
    const creds = await importServiceCredentials();
    const resendKey = creds.resend_api_key;
    
    if (!resendKey || resendKey === "" || resendKey === "YOUR_RESEND_KEY") {
      // If no Resend key, save to local CSV as fallback
      await saveEmailLocally(email, source);
      return new Response(JSON.stringify({ 
        success: true, 
        message: "Email saved. We'll notify you when Pro launches.",
        pending: true 
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Send confirmation email via Resend
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${resendKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: "Uzi Network <onboarding@resend.dev>", // Replace with verified domain
        to: [email],
        subject: "You're on the list! 👋",
        html: `
          <!DOCTYPE html>
          <html>
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Uzi Network</title>
          </head>
          <body style="margin: 0; padding: 0; background-color: #0f0f0f; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <tr>
                <td style="background-color: #1a1a1a; border-radius: 12px; padding: 40px 30px;">
                  
                  <!-- Logo/Header -->
                  <div style="text-align: center; margin-bottom: 30px;">
                    <div style="font-size: 32px; font-weight: 900; color: #ffffff; letter-spacing: -1px;">UZI NETWORK</div>
                    <div style="font-size: 14px; color: #00d970; letter-spacing: 2px; text-transform: uppercase;">AI TOOLS & REVIEWS</div>
                  </div>
                  
                  <!-- Greeting -->
                  <h1 style="font-size: 24px; font-weight: 700; color: #ffffff; margin: 0 0 20px 0;">You're on the list! 👋</h1>
                  
                  <p style="font-size: 16px; color: #a1a1aa; line-height: 1.6; margin: 0 0 20px 0;">
                    <strong>Hey there,</strong>
                  </p>
                  
                  <p style="font-size: 16px; color: #a1a1aa; line-height: 1.6; margin: 0 0 20px 0;">
                    You just joined <strong>${email}</strong> and you're one step closer to saving serious money on AI tools.
                  </p>
                  
                  <!-- What happens next -->
                  <div style="background-color: #0a0a0a; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <p style="font-size: 14px; color: #00d970; font-weight: 600; margin: 0 0 10px 0;">WHAT'S NEXT:</p>
                    <ul style="font-size: 14px; color: #a1a1aa; line-height: 1.6; margin: 0; padding-left: 20px;">
                      <li style="margin-bottom: 6px;">✅ We'll email you when Pro subscriptions open</li>
                      <li style="margin-bottom: 6px;">📧 You'll get our weekly newsletter: "The Drops"</li>
                      <li>🎫 Exclusive discount codes for AI tools you use</li>
                    </ul>
                  </div>
                  
                  <!-- Pro tier teaser -->
                  <div style="background: linear-gradient(135deg, #00d970 0%, #00b359 100%); border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                    <p style="font-size: 14px; color: #000000; font-weight: 600; margin: 0 0 8px 0;">PRO COMING SOON</p>
                    <p style="font-size: 12px; color: #333333; margin: 0;">For $9/month — exclusive discount codes, deep-dives, and more</p>
                  </div>
                  
                  <!-- Links -->
                  <div style="text-align: center; margin: 30px 0;">
                    <a href="https://uzi.network.store" style="display: inline-block; background-color: #ffffff; color: #000000; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 14px;">
                      Visit Uzi Network →
                    </a>
                  </div>
                  
                  <!-- Footer -->
                  <p style="font-size: 12px; color: #71717a; text-align: center; margin: 20px 0 0 0;">
                    You're receiving this because you signed up at <a href="https://uzi.network.store" style="color: #00d970; text-decoration: none;">uzi.network.store</a>
                  </p>
                  <p style="font-size: 12px; color: #71717a; text-align: center; margin: 10px 0 0 0;">
                    <a href="%%UNSUBSCRIBE_URL%%" style="color: #71717a; text-decoration: underline;">Unsubscribe</a>
                  </p>
                  
                </td>
              </tr>
            </table>
          </body>
          </html>
        `,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      return new Response(JSON.stringify({ 
        success: true, 
        message: "Thanks! You'll get an email when Pro launches.",
        pending: false 
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    } else {
      // Fallback to local save if Resend fails
      await saveEmailLocally(email, source);
      return new Response(JSON.stringify({ 
        success: true, 
        message: "Email saved locally. We'll notify you when Pro launches.",
        pending: true 
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
  } catch (error) {
    return new Response(JSON.stringify({ error: "Failed to process" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

async function importServiceCredentials() {
  // Read from .service-credentials file on the server
  try {
    const fs = await import("node:fs/promises");
    const path = await import("node:path");
    const credsPath = "/home/ubuntu/.hermes/.service-credentials";
    const content = await fs.readFile(credsPath, "utf-8");
    
    const env = {};
    const lines = content.split("\n");
    for (const line of lines) {
      if (line.startsWith("export ")) {
        const match = line.match(/export\s+([A-Z_][A-Z0-9_]*)=["']?([^"']*)["']?/);
        if (match) {
          env[match[1].toLowerCase()] = match[2];
        }
      }
    }
    return env;
  } catch {
    return {};
  }
}

async function saveEmailLocally(email, source) {
  try {
    const fs = await import("node:fs/promises");
    const path = await import("node:path");
    
    const dataDir = "/home/ubuntu/projects/uzi-network/data/subscribers";
    const filePath = path.join(dataDir, "subscribers.csv");
    
    // Ensure directory exists
    await fs.mkdir(dataDir, { recursive: true });
    
    // Check if file exists
    let content = "";
    try {
      content = await fs.readFile(filePath, "utf-8");
    } catch {
      content = "";
    }
    
    // Add if not duplicate
    const lines = content.split("\n").filter(l => l.trim());
    if (!lines.some(l => l.startsWith(email + ","))) {
      const timestamp = new Date().toISOString();
      await fs.appendFile(filePath, `\n${email},${source},${timestamp}`);
    }
  } catch (error) {
    console.error("Failed to save email locally:", error);
  }
}
