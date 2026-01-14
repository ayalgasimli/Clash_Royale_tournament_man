# Clash Royale REST API Specification

Clash Royale exposes a RESTful HTTPS API that returns JSON data about players, battles, cards, and other game entities. This document summarizes the key endpoints referenced in this project with emphasis on player-related data and card catalog lookups.

---

## 1. Base Information

| Item            | Value / Notes                                                                 |
|-----------------|-------------------------------------------------------------------------------|
| Base URL        | `https://api.clashroyale.com/v1`                                              |
| Transport       | HTTPS only                                                                    |
| Content types   | Request: `application/json`; Response: `application/json`                     |
| Authentication  | Bearer token (Supercell developer portal). Include `Authorization: Bearer …`. |
| Rate limits     | Enforced per API key and IP. Typical caps are 10 req/sec and 5000 req/day.    |
| Error model     | `ClientError` JSON with `reason`, `message`, `type`, `detail`.                 |

> **Note:** Always whitelist the source IP when generating the API key. Calls from unlisted IPs receive `403`.

---

## 2. Common HTTP Status Codes

| Code | Meaning                                                                                                   |
|------|-----------------------------------------------------------------------------------------------------------|
| 200  | Success. Body structure depends on endpoint.                                                              |
| 400  | Invalid parameters. Check tag formatting (uppercase, without `#` in path).                                |
| 403  | Unauthorized: missing/expired key or wrong IP.                                                            |
| 404  | Resource not found (e.g., player tag does not exist).                                                     |
| 429  | Rate limited. Reduce request rate or add caching/polling backoff.                                         |
| 500  | Internal API error. Retry after delay.                                                                    |
| 503  | Service unavailable (maintenance). Retry using exponential backoff.                                       |

---

## 3. Authorization Workflow

1. Create an account at [https://developer.clashroyale.com](https://developer.clashroyale.com).
2. Generate an API key and whitelist the public IP of the machine/server making requests.
3. Store the key securely (environment variable, secret store).  
4. Attach the key on every request:

```
Authorization: Bearer <YOUR_LONG_TOKEN>
Accept: application/json
```

---

## 4. Endpoint Reference

### 4.1 Get Player Profile

|                |                                                                                        |
|----------------|----------------------------------------------------------------------------------------|
| Method         | `GET`                                                                                  |
| Path           | `/players/{playerTag}`                                                                 |
| Path params    | `playerTag` (string, required) – player tag **without** the `#`.                       |
| Description    | Retrieves trophy count, favorite card, best ranks, and clan info for a single player. |

**Example request**

```
GET /v1/players/%232CCCP
Authorization: Bearer <TOKEN>
```

**Response body (abridged)**

```json
{
  "tag": "#2CCCP",
  "name": "Chief Pat",
  "trophies": 7000,
  "bestTrophies": 7600,
  "expLevel": 50,
  "wins": 3000,
  "losses": 2900,
  "clan": {
    "tag": "#8CL",
    "name": "Tribe Gaming",
    "badgeId": 16000000
  },
  "currentFavouriteCard": {
    "id": 26000056,
    "name": "Mega Knight",
    "maxLevel": 14
  },
  "leagueStatistics": {
    "bestSeason": { "id": "2023-10", "rank": 1200, "trophies": 8000 }
  }
}
```

---

### 4.2 Get Player Upcoming Chests

|                |                                                                                              |
|----------------|------------------------------------------------------------------------------------------------|
| Method         | `GET`                                                                                          |
| Path           | `/players/{playerTag}/upcomingchests`                                                          |
| Path params    | `playerTag` (string, required)                                                                 |
| Description    | Returns the next 10 chests the player will unlock, including Super Magical, Legendary, etc. |

**Example request**

```
GET /v1/players/%232CCCP/upcomingchests
Authorization: Bearer <TOKEN>
```

**Response body (abridged)**

```json
{
  "items": [
    { "index": 0, "name": "Silver Chest" },
    { "index": 2, "name": "Golden Chest" },
    { "index": 8, "name": "Magical Chest" }
  ],
  "paging": {
    "cursors": { "after": "eyJpZHgiOjEw..." }
  }
}
```

---

### 4.3 Get Player Battle Log

|                |                                                                                                                                |
|----------------|--------------------------------------------------------------------------------------------------------------------------------|
| Method         | `GET`                                                                                                                          |
| Path           | `/players/{playerTag}/battlelog`                                                                                                |
| Path params    | `playerTag` (string, required)                                                                                                 |
| Description    | Returns the 25 most recent battles, including opponent info, decks, timestamps, and crown counts.                           |
| Notes          | This endpoint is frequently rate-limited—queue requests and cache responses for several minutes.                               |

**Example request**

```
GET /v1/players/%232CCCP/battlelog
Authorization: Bearer <TOKEN>
```

**Response body (per battle entry, abridged)**

```json
[
  {
    "type": "tournament",
    "battleTime": "20240101T101234.000Z",
    "arena": {
      "id": 54000012,
      "name": "Master II",
      "iconUrls": { "medium": "https://..." }
    },
    "gameMode": { "id": 72000019, "name": "1v1" },
    "team": [
      {
        "tag": "#2CCCP",
        "name": "Chief Pat",
        "crowns": 3,
        "startingTrophies": 7000,
        "cards": [
          { "name": "Mega Knight", "level": 14, "maxLevel": 14 }
        ]
      }
    ],
    "opponent": [
      {
        "tag": "#P0N0",
        "name": "Opponent",
        "crowns": 1,
        "cards": [
          { "name": "P.E.K.K.A", "level": 14 }
        ]
      }
    ],
    "challengeId": 0,
    "isHostedMatch": true
  }
]
```

**Enumerations (selected fields)**

| Field              | Sample values                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------------|
| `deckSelection`    | `COLLECTION`, `DRAFT`, `PICK`, `UNKNOWN`                                                           |
| `type`             | `TOURNAMENT`, `FRIENDLY`, `CLANMATE`, `PVP`, `PVE`, `EVENT`                                        |
| `boatBattleSide`   | `attacker`, `defender`                                                                             |
| `isHostedMatch`    | Boolean – `true` when the match originates from a hosted tournament or friendly battle.           |

#### 4.3.1 Battle Log Models

Each element in the array returned by `/players/{tag}/battlelog` is a **Battle** object. The API nests several reusable models; the tables below catalog every property exposed by Supercell’s schema.

##### Battle

| Field                     | Type                      | Description                                                                                                   |
|---------------------------|---------------------------|---------------------------------------------------------------------------------------------------------------|
| `arena`                   | [`Arena`](#arena)         | Arena metadata (ID, localized name, icons).                                                                   |
| `gameMode`                | [`GameMode`](#gamemode)   | Identifier/name of the game mode used (e.g., Ladder, Draft, Clan War).                                       |
| `leagueNumber`            | `integer`                 | Player league number for the match (Path of Legends).                                                         |
| `deckSelection`           | `string (enum)`           | Ruleset for deck selection. Values: `COLLECTION`, `DRAFT`, `DRAFT_COMPETITIVE`, `PREDEFINED`, `EVENT_DECK`, `PICK`, `WARDECK_PICK`, `QUADDECK_PICK`, `UNKNOWN`. |
| `challengeWinCountBefore` | `integer`                 | Wins the player had before the challenge battle.                                                              |
| `boatBattleSide`          | `string`                  | `attacker` or `defender` in River Raid boat battles.                                                          |
| `newTowersDestroyed`      | `integer`                 | Towers destroyed in the current battle.                                                                       |
| `prevTowersDestroyed`     | `integer`                 | Towers destroyed in the previous battle (boat battles).                                                       |
| `remainingTowers`         | `integer`                 | Remaining towers after the fight (boat battles).                                                              |
| `boatBattleWon`           | `boolean`                 | Whether the boat skirmish was won.                                                                            |
| `type`                    | `string (enum)`           | Battle type. Possible values include `PVP`, `PVE`, `CLANMATE`, `TOURNAMENT`, `FRIENDLY`, `SURVIVAL`, `PVP2v2`, `CLANMATE2v2`, `CHALLENGE2v2`, `CLANWAR_COLLECTION_DAY`, `CLANWAR_WAR_DAY`, `CASUAL_1V1`, `CASUAL_2V2`, `BOAT_BATTLE`, `RIVER_RACE_PVP`, `RIVER_RACE_DUEL`, `PATH_OF_LEGEND`, `TUTORIAL`, `SEASONAL_BATTLE`, `PRACTICE`, `TRAIL`, `UNKNOWN`. |
| `isHostedMatch`           | `boolean`                 | `true` if created via tournament/friendly host tools.                                                         |
| `isLadderTournament`      | `boolean`                 | Indicates if the battle counted toward a hosted ladder tournament.                                            |
| `challengeId`             | `integer`                 | ID of the challenge (0 when not applicable).                                                                  |
| `challengeTitle`          | `string`                  | Display title of the challenge/event.                                                                         |
| `tournamentTag`           | `string`                  | Tag of the tournament (if applicable).                                                                        |
| `eventTag`                | `string`                  | Tag of the event for event battles.                                                                           |
| `battleTime`              | `string (UTC)`            | Timestamp in format `YYYYMMDDTHHmmss.000Z`.                                                                   |
| `team`                    | [`PlayerBattleData[]`](#playerbattledata) | Array describing the player/team side (1 element for 1v1, 2 for 2v2).                                        |
| `opponent`                | [`PlayerBattleData[]`](#playerbattledata) | Array describing the opposing side.                                                                           |

##### Arena

| Field    | Type                  | Description                                              |
|----------|-----------------------|----------------------------------------------------------|
| `id`     | `integer`             | Arena ID.                                                |
| `name`   | [`JsonLocalizedName`](#jsonlocalizedname) | Localized arena name object.                            |
| `rawName`| `string`              | Internal identifier (e.g., `Arena_L3`).                  |
| `iconUrls` | `object`            | Map of icon sizes (`small`, `medium`, `large`).          |

##### GameMode

| Field | Type     | Description                                          |
|-------|----------|------------------------------------------------------|
| `id`  | `integer`| Mode identifier (e.g., `72000007`).                  |
| `name`| `string` | Localized name (e.g., `Friendly`).                   |

##### PlayerBattleData

| Field                      | Type                                          | Description                                                                 |
|----------------------------|-----------------------------------------------|-----------------------------------------------------------------------------|
| `tag`                      | `string`                                      | Player tag (with `#`).                                                      |
| `name`                     | `string`                                      | Player name.                                                                |
| `clan`                     | [`PlayerClan`](#playerclan)                   | Clan info; absent if player is clanless.                                    |
| `cards`                    | [`PlayerItemLevel[]`](#playeritemlevel)       | Eight cards from the battle deck.                                           |
| `supportCards`             | [`PlayerItemLevel[]`](#playeritemlevel)       | Extra cards for certain modes (e.g., deck picks).                           |
| `elixirLeaked`             | `float`                                       | Total elixir leaked during battle (rarely populated).                       |
| `globalRank`               | `integer`                                     | Player’s global rank at battle time (if applicable).                        |
| `crowns`                   | `integer`                                     | Crown count earned in this battle.                                          |
| `startingTrophies`         | `integer`                                     | Trophy count prior to match.                                                |
| `trophyChange`             | `integer`                                     | Trophy delta after battle (0 for friendlies).                               |
| `kingTowerHitPoints`       | `integer`                                     | Remaining HP of the king tower.                                            |
| `princessTowersHitPoints`  | `integer[]`                                   | HP of each princess tower after battle.                                     |
| `rounds`                   | [`PlayerBattleRound[]`](#playerbattleround)   | Round outcomes for duel/war multi-round modes.                              |
| `deckLink`                 | `string`                                      | Shareable deck link (if provided).                                          |

##### PlayerClan

| Field     | Type     | Description                                   |
|-----------|----------|-----------------------------------------------|
| `tag`     | `string` | Clan tag.                                     |
| `name`    | `string` | Clan name.                                    |
| `badgeId` | `integer`| Badge identifier.                             |
| `badgeUrls` | `object` | Icon URLs for the clan badge (optional).   |

##### PlayerItemLevel

| Field                | Type     | Description                                                                    |
|----------------------|----------|--------------------------------------------------------------------------------|
| `name`               | `string` | Card name (e.g., `Firecracker`).                                               |
| `id`                 | `integer`| Card ID.                                                                       |
| `level`              | `integer`| Effective level used in battle.                                                |
| `maxLevel`           | `integer`| Max level for the card’s rarity.                                               |
| `maxEvolutionLevel`  | `integer`| Max evolution tier (if card has evolutions).                                   |
| `rarity`             | `string` | `common`, `rare`, `epic`, `legendary`, `champion`, etc.                        |
| `elixirCost`         | `integer`| Elixir cost of the card.                                                       |
| `iconUrls`           | `object` | Icon links for regular, hero, or evolution states (`medium`, `evolutionMedium`). |

##### PlayerBattleRound

| Field         | Type     | Description                                          |
|---------------|----------|------------------------------------------------------|
| `roundIndex`  | `integer`| Round number within the duel/war.                    |
| `roundStar`   | `integer`| Star indicator (`0`, `1`, `2`, or `3`).              |
| `roundWinner` | `string` | `team` or `opponent`.                                |

##### JsonLocalizedName

| Field     | Type     | Description                                                               |
|-----------|----------|---------------------------------------------------------------------------|
| `name`    | `string` | Localized text.                                                           |
| `id`      | `integer`| Localized string identifier.                                              |
| `languageCode` | `string` | Language code (e.g., `en`, `es`, `tr`).                             |

These models mirror Supercell’s documented schema and align with the responses captured when calling the live API (see verification logs). Use them to shape TypeScript interfaces or database schemas when persisting battle-log data.

---

### 4.4 Get Card Catalog

|                |                                                                      |
|----------------|----------------------------------------------------------------------|
| Method         | `GET`                                                                |
| Path           | `/cards`                                                             |
| Query params   | `limit` (int, optional), `after` (string), `before` (string)         |
| Description    | Returns the full list of collectible cards plus support cards.      |

**Example request**

```
GET /v1/cards?limit=50
Authorization: Bearer <TOKEN>
```

**Response body (abridged)**

```json
{
  "items": [
    {
      "id": 26000000,
      "name": "Knight",
      "maxLevel": 14,
      "rarity": "Common",
      "elixirCost": 3,
      "iconUrls": {
        "medium": "https://api-assets.clashroyale.com/cards/knight.png"
      }
    }
  ],
  "supportItems": [],
  "paging": {
    "cursors": { "after": "eyJpZHgiOjUw..."}
  }
}
```

**Pagination**

- `limit`: max items per page (default 50, max 200).  
- `after` / `before`: pass the cursor from the previous response’s `paging.cursors`. Only one cursor can be supplied at a time.

---

## 5. Error Payload (ClientError)

```json
{
  "reason": "accessDenied",
  "message": "Access denied, invalid credentials",
  "type": "accessDenied",
  "detail": {
    "traceId": "abcd-1234"
  }
}
```

Fields:

- `reason`: short code (e.g., `badRequest`, `accessDenied`, `notFound`, `tooManyRequests`).  
- `message`: human-readable explanation.  
- `type`: duplicate of `reason` for legacy clients.  
- `detail`: optional metadata (trace IDs, invalid parameter names).

---

## 6. Best Practices

1. **Normalize player tags**: uppercase, strip whitespace, remove `#` before building the URL (`%23` is URL encoding for `#`).  
2. **Backoff on 429/503**: use exponential backoff with jitter and log the incidents for quota planning.  
3. **Cache immutable data**: card lists change rarely—cache for hours. Player info can be cached for a few minutes to spare quota.  
4. **Store battle logs**: the API only returns recent battles; persist what you need for historical analytics.  
5. **Secure the key**: never expose the bearer token in client-side code; route requests through a trusted proxy (e.g., `api.py`).

---

## 7. Glossary

| Term            | Definition                                                                                      |
|-----------------|-------------------------------------------------------------------------------------------------|
| Battle Log      | A chronological list of matches returned by `/players/{tag}/battlelog`.                         |
| Hosted Match    | Tournament/friendly battle triggered outside regular ladder.                                     |
| Support Items   | Cosmetic or event items associated with cards (emotes, banners).                                |
| Cursor          | Base64 cursor string used for pagination on list endpoints (e.g., cards, clans).                |

---

This specification covers the subset of endpoints leveraged by the Clash Royale Tournament Manager project. Consult the official Supercell documentation for additional endpoints such as clans, tournaments, or river race data.
