# Dynamic AI MP Patch Notes

## 1.19.2.4

### Compatibility

- Updated for Hearts of Iron IV 1.19.3. Merged the 1.19.3 changes to doctrines, technologies, German decisions and focuses, and British MIOs.

### Germany

- Historical Germany now keeps extra factories on infantry, support, and artillery equipment from the start of the game until it goes to war. This helps its army reach the manpower that Demand Sudetenland, Molotov-Ribbentrop, and Danzig or War require, so the war with Poland starts closer to the historical date.

### Soviet Union

- When preparing for or fighting a war while holding Leningrad, the Soviets now prioritize naval missions in the Gulf of Finland, Gulf of Bothnia, and Lower Baltic Sea. The naval AI still decides whether task forces are available to fill those missions.
- The Soviets are no longer discouraged from naval landings in Finland.
- The Soviet civilian factory construction push now targets 135 civilian factories. It still runs only before 1939 and while at peace.
- The Soviets now research signal companies early, so their infantry divisions can use them.

### Japan, Manchukuo, and Mengjiang

- Manchukuo now guards Mengjiang's border while Mengjiang has not lost a state. If Mengjiang loses a state, Japan defends it again.
- Home-island defense is split into northern, central, and southern Japan, so the north is no longer left thin. Japan keeps a light garrison during a war with a major naval power. It raises that garrison sharply for 60 days whenever enemy surface fleets appear in the Sea of Japan, the Coast of Japan, or the East China Sea; submarines and China's fleet do not count. During those periods, Manchukuo and Mengjiang also send troops to northern Japan.
- Japan's scripted unit-spawn decision is disabled for now.

### Division Templates

- Non-major, Japanese, and Chinese infantry use infantry guns until 1940, then switch to heavy weapons companies.
- Japanese infantry adds engineers, anti-air, anti-tank, and logistics support from 1940.
- Chinese infantry is simplified to a 9-battalion division with artillery until 1940, then the standard 18-width infantry division. The larger 11-battalion divisions are removed.
- Armored divisions use regular engineers until the Military Engineering Vehicles special project unlocks armored engineers, then switch to armored engineers.
- The 25-battalion garrison division is now limited to majors. From 1940, majors that build tanks fill it with light tanks instead of cavalry. Light tanks need half the manpower and lose far less equipment and manpower to resistance attacks.

### Equipment Designs

- Light tanks are no longer a main armor option. The only light tank design the AI builds is a cheap machine-gun tank (one-man turret, riveted armor, no upgrades), used for garrisons and light tank support companies.
- Fixed 79 invalid bomber design entries in the medium and heavy aircraft designs. These designs now require the special modules they list.

### Other

- Internal cleanup of trade, German state development, Sea Lion, and D-Day scripting, with no intended behavior change.
