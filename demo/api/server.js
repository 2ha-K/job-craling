import dns from "node:dns";
import path from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import express from "express";
import { MongoClient, ObjectId } from "mongodb";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "../..");

dotenv.config({ path: path.join(projectRoot, ".env") });

const app = express();
const port = Number(process.env.DEMO_API_PORT || 4141);
const mongoUrl = process.env.MONGO_URL;
const dbName = process.env.MONGO_DB;
const localDevOrigin = /^http:\/\/(?:127\.0\.0\.1|localhost):\d+$/;

if (mongoUrl?.startsWith("mongodb+srv://")) {
  const dnsServers = (process.env.DEMO_DNS_SERVERS || "1.1.1.1,8.8.8.8")
    .split(",")
    .map((server) => server.trim())
    .filter(Boolean);
  dns.setServers(dnsServers);
}

let client;
let collection;

app.use((req, res, next) => {
  const origin = req.get("origin");
  if (origin && localDevOrigin.test(origin)) {
    res.set("Access-Control-Allow-Origin", origin);
    res.set("Vary", "Origin");
  }
  res.set("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.set("Access-Control-Allow-Headers", "Content-Type");

  if (req.method === "OPTIONS") {
    res.sendStatus(204);
    return;
  }

  next();
});

async function getCollection() {
  if (!mongoUrl || !dbName) {
    throw new Error("Missing MONGO_URL or MONGO_DB in project .env");
  }

  if (!collection) {
    client = new MongoClient(mongoUrl);
    await client.connect();
    collection = client.db(dbName).collection("posts");
  }

  return collection;
}

function serializePost(post) {
  return {
    ...post,
    _id: post._id?.toString?.() || post._id,
  };
}

app.get("/api/health", async (_req, res) => {
  try {
    await getCollection();
    res.json({ ok: true, database: dbName, collection: "posts" });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

app.get("/api/posts", async (req, res) => {
  try {
    const posts = await getCollection();
    const limit = Math.min(Number(req.query.limit || 120), 300);
    const search = String(req.query.search || "").trim();
    const group = String(req.query.group || "").trim();

    const filter = {};
    if (search) {
      filter.$or = [
        { author: { $regex: search, $options: "i" } },
        { content: { $regex: search, $options: "i" } },
        { group_name: { $regex: search, $options: "i" } },
      ];
    }
    if (group) {
      filter.group_name = group;
    }

    const data = await posts
      .find(filter)
      .sort({ datetime: -1, _id: -1 })
      .limit(limit)
      .toArray();

    res.json({ posts: data.map(serializePost) });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get("/api/posts/:id", async (req, res) => {
  try {
    const posts = await getCollection();
    const post = await posts.findOne({ _id: new ObjectId(req.params.id) });

    if (!post) {
      res.status(404).json({ error: "Post not found" });
      return;
    }

    res.json({ post: serializePost(post) });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, "127.0.0.1", () => {
  console.log(`BLACKBOX API listening on http://127.0.0.1:${port}`);
});
