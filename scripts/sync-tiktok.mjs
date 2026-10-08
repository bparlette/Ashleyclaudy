#!/usr/bin/env node
// Sync Ashley's latest TikTok videos into content/fan.json
// Uses yt-dlp to fetch the channel's recent videos (no API key needed)
//
// Usage:
//   node scripts/sync-tiktok.mjs              # update fan.json with latest videos
//   node scripts/sync-tiktok.mjs --dry-run    # show what would change

import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const FAN_JSON = path.join(ROOT, "content/fan.json");
const DRY = process.argv.includes("--dry-run");
const CHANNEL = "https://www.tiktok.com/@ashley.claudy";
const MAX_VIDEOS = 9;

function getLatestVideos() {
  try {
    const out = execSync(
      `yt-dlp --flat-playlist --print "%(id)s|%(title)s|%(like_count)s" "${CHANNEL}" 2>/dev/null | head -${MAX_VIDEOS}`,
      { encoding: "utf8", timeout: 60000 }
    );
    return out.trim().split("\n").filter(Boolean).map(line => {
      const [id, title, likes] = line.split("|");
      return { id, title: title || "", likes: likes || "" };
    });
  } catch (e) {
    console.error("Failed to fetch TikTok videos:", e.message.slice(0, 100));
    return null;
  }
}

function formatLikes(n) {
  n = Number(n);
  if (!n) return "";
  if (n >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
  return String(n);
}

async function main() {
  const videos = getLatestVideos();
  if (!videos) {
    console.log("Could not fetch videos, leaving fan.json alone.");
    return;
  }

  const fan = JSON.parse(fs.readFileSync(FAN_JSON, "utf8"));
  const existing = new Map((fan.social_posts || []).map(p => {
    const m = (p.url || "").match(/video\/(\d+)/);
    return [m ? m[1] : p.url, p];
  }));

  let added = 0, updated = 0;
  const newPosts = [];

  for (const v of videos) {
    const url = `https://www.tiktok.com/@ashley.claudy/video/${v.id}`;
    const existing_post = existing.get(v.id);

    if (existing_post) {
      // Update likes if changed
      const likes = formatLikes(v.likes);
      if (likes && existing_post.likes !== likes) {
        existing_post.likes = likes;
        updated++;
      }
      newPosts.push(existing_post);
    } else {
      // New video — add it (thumb will be generated separately)
      newPosts.push({
        platform: "tiktok",
        url,
        caption: v.title.slice(0, 80),
        thumb: `assets/social/${v.id}.jpg`,
        likes: formatLikes(v.likes),
        show: true,
      });
      added++;
      console.log(`  + New: ${v.id} "${v.title.slice(0, 40)}"`);
    }
  }

  // Keep non-tiktok posts
  const otherPosts = (fan.social_posts || []).filter(p => p.platform !== "tiktok");
  fan.social_posts = [...newPosts, ...otherPosts];
  fan._updated = new Date().toISOString().split("T")[0];

  if ((added > 0 || updated > 0) && !DRY) {
    fs.writeFileSync(FAN_JSON, JSON.stringify(fan, null, 2) + "\n");
    console.log(`\nUpdated fan.json: ${added} added, ${updated} like-counts updated.`);
  } else if (DRY) {
    console.log(`\n[dry run] Would add ${added}, update ${updated}.`);
  } else {
    console.log("\nNo changes needed.");
  }
}

main();
