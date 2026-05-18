enum Face { U, D, L, R, F, B };

const int motors[6][3] = {
  {13, 14, 33}, // 0: U
  {26, 25, 27}, // 1: D
  {32, 15, 19}, // 2: L
  {23, 22, 18}, // 3: R
  {4, 2, 5},    // 4: F
  {12, 21, 17}  // 5: B
};

int steps90[6] = {1625, 1625, 815, 815, 810, 800};

const int SIDE_START_DELAY = 800;
const int SIDE_TARGET_DELAY = 100;
const int SIDE_RAMP = 200;
const int UD_START_DELAY = 800;
const int UD_TARGET_DELAY = 100;
const int UD_RAMP = 200;
const int BRAKE_TIME = 100;

// Struct to hold pattern information
struct CubePattern {
  const char* name;
  const char* sequence;
};

// 16 Famous Rubik's Cube Patterns
const CubePattern patterns[16] = {
  {"Checkerboard", "U2 D2 L2 R2 F2 B2"},
  {"6-Spot (Dots)", "U D' R L' F B' U' D"},
  {"4-Spot", "F2 B2 R2 L2"},
  {"Cube in a Cube", "F L F U' R U F2 L2 U' L' B D' B' L2 U"},
  {"Cube in a Cube in a Cube", "U' L' U' F' R2 B' R F U B2 U' B' R' R' L F' U"},
  {"Anaconda", "L U B' U' R L' B R' F B' D R D' F'"},
  {"Python", "F2 R' B' U R' L F' L F' B D' R2 B2 L2"},
  {"Black Hole", "R2 L2 U2 D2 F2 B2 U' D R2 L2 F2 B2 U D'"},
  {"Crosses", "R2 L2 U2 D2 F2 B2 R L' U D' F B'"},
  {"Plummer's Cross", "R2 L2 F2 B2 U2 D2 R2 L2 F2 B2"},
  {"Gift Box", "U B2 D2 F2 D2 B2 D2 F2 R2 D2 R2 U'"},
  {"Twisted Duck", "F R' B R U F' L' U' D2 R D' F' B R'"},
  {"Green Core", "U2 R2 F2 B2 L2 D2 R2 F2 B2 L2"},
  {"Exchanged Chicken Feet", "F2 R2 F2 R2 U2 F2 R2 F2 R2 U2"},
  {"Spiral", "L' B' D U R F' R' D' U' B L U2"},
  {"Tent", "U2 F2 R2 D2 R2 F2 U2"}
};

// Global tracking state for our application menu
enum MenuState { SHOW_MAIN_MENU, WAIT_MAIN_CHOICE, WAIT_STRING_INPUT, WAIT_PATTERN_CHOICE };
MenuState menuState = SHOW_MAIN_MENU;

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 6; i++) {
    pinMode(motors[i][0], OUTPUT);
    pinMode(motors[i][1], OUTPUT);
    pinMode(motors[i][2], OUTPUT);
    digitalWrite(motors[i][2], HIGH);
  }
  Serial.println("--- System Ready (Parallel Moves & U2/D2 Split Enabled) ---");
}

int getAxis(int faceIdx) {
  return faceIdx / 2;
}

void moveParallel(int m1, int q1, bool cw1, int m2 = -1, int q2 = 0, bool cw2 = true) {
  long steps1 = (m1 != -1) ? (long)steps90[m1] * q1 : 0;
  long steps2 = (m2 != -1) ? (long)steps90[m2] * q2 : 0;

  long current1 = 0, current2 = 0;
  unsigned long nextMicros1 = micros();
  unsigned long nextMicros2 = micros();

  int startDelay1 = 0, limitSpeed1 = 0, rampSteps1 = 0;
  if (m1 != -1) {
    startDelay1 = (m1 == U || m1 == D) ? UD_START_DELAY : SIDE_START_DELAY;
    int targetDelay = (m1 == U || m1 == D) ? UD_TARGET_DELAY : SIDE_TARGET_DELAY;
    limitSpeed1 = (m1 == U || m1 == D || m1 == B) ? targetDelay / 2 : targetDelay;
    rampSteps1 = (m1 == U || m1 == D) ? UD_RAMP : SIDE_RAMP;

    digitalWrite(motors[m1][2], LOW);
    digitalWrite(motors[m1][1], cw1 ? HIGH : LOW);
  }

  int startDelay2 = 0, limitSpeed2 = 0, rampSteps2 = 0;
  if (m2 != -1) {
    startDelay2 = (m2 == U || m2 == D) ? UD_START_DELAY : SIDE_START_DELAY;
    int targetDelay = (m2 == U || m2 == D) ? UD_TARGET_DELAY : SIDE_TARGET_DELAY;
    limitSpeed2 = (m2 == U || m2 == D || m2 == B) ? targetDelay / 2 : targetDelay;
    rampSteps2 = (m2 == U || m2 == D) ? UD_RAMP : SIDE_RAMP;

    digitalWrite(motors[m2][2], LOW);
    digitalWrite(motors[m2][1], cw2 ? HIGH : LOW);
  }

  if (m1 != -1 || m2 != -1) delay(10);

  while (current1 < steps1 || current2 < steps2) {
    unsigned long now = micros();

    if (current1 < steps1 && now >= nextMicros1) {
      digitalWrite(motors[m1][0], HIGH);
      delayMicroseconds(2);
      digitalWrite(motors[m1][0], LOW);

      int currentDelay = (current1 < rampSteps1)
          ? startDelay1 - ((startDelay1 - limitSpeed1) * current1 / rampSteps1)
          : limitSpeed1;

      nextMicros1 = now + (currentDelay * 2);
      current1++;
    }

    if (current2 < steps2 && now >= nextMicros2) {
      digitalWrite(motors[m2][0], HIGH);
      delayMicroseconds(2);
      digitalWrite(motors[m2][0], LOW);

      int currentDelay = (current2 < rampSteps2)
          ? startDelay2 - ((startDelay2 - limitSpeed2) * current2 / rampSteps2)
          : limitSpeed2;

      nextMicros2 = now + (currentDelay * 2);
      current2++;
    }
  }

  delay(BRAKE_TIME);
  if (m1 != -1) digitalWrite(motors[m1][2], HIGH);
  if (m2 != -1) digitalWrite(motors[m2][2], HIGH);
}

void executeMovePair(int m1, int q1, bool cw1, int m2, int q2, bool cw2) {
  bool split1 = ((m1 == U || m1 == D) && q1 == 2);
  bool split2 = ((m2 == U || m2 == D) && q2 == 2);

  if (split1 || split2) {
    int p1 = split1 ? 1 : q1;
    int p2 = split2 ? 1 : q2;
    moveParallel(m1, p1, cw1, m2, p2, cw2);

    delay(50);

    int rem1 = split1 ? 1 : 0;
    int rem2 = split2 ? 1 : 0;

    if (rem1 > 0 || rem2 > 0) {
      moveParallel((rem1 > 0 ? m1 : -1), rem1, cw1,
                   (rem2 > 0 ? m2 : -1), rem2, cw2);
    }
  } else {
    moveParallel(m1, q1, cw1, m2, q2, cw2);
  }
}

void executeSequence(String cmd) {
  cmd.trim();
  cmd += " ";

  int prevFace = -1, prevQ = 0;
  bool prevCw = true;

  String currentToken = "";
  for (unsigned int i = 0; i < cmd.length(); i++) {
    char c = cmd.charAt(i);

    if (c != ' ') {
      currentToken += c;
    } else if (currentToken.length() > 0) {
      char faceChar = toupper(currentToken.charAt(0));
      int faceIdx = -1;
      if (faceChar == 'U') faceIdx = U;
      else if (faceChar == 'D') faceIdx = D;
      else if (faceChar == 'L') faceIdx = L;
      else if (faceChar == 'R') faceIdx = R;
      else if (faceChar == 'F') faceIdx = F;
      else if (faceChar == 'B') faceIdx = B;

      if (faceIdx != -1) {
        int q = 1;
        bool cw = true;
        if (currentToken.length() > 1) {
          if (currentToken.charAt(1) == '2') q = 2;
          else if (currentToken.charAt(1) == '\'') cw = false;
        }

        if (prevFace != -1 && getAxis(prevFace) == getAxis(faceIdx)) {
          executeMovePair(prevFace, prevQ, prevCw, faceIdx, q, cw);
          prevFace = -1;
        } else {
          if (prevFace != -1) {
            executeMovePair(prevFace, prevQ, prevCw, -1, 0, true);
          }
          prevFace = faceIdx;
          prevQ = q;
          prevCw = cw;
        }
      }
      currentToken = "";
    }
  }
  if (prevFace != -1) {
    executeMovePair(prevFace, prevQ, prevCw, -1, 0, true);
  }
}

void scrambleCube(int n) {
  Serial.print("Scrambling with ");
  Serial.print(n);
  Serial.println(" moves...");

  int lastFace = -1;

  for (int i = 0; i < n; i++) {
    int faceIdx;
    do {
      faceIdx = random(0, 6);
    } while (faceIdx == lastFace);
    lastFace = faceIdx;

    int r = random(0, 3);
    int q = (r == 1) ? 2 : 1;
    bool cw = (r != 2);

    const char* faceNames[] = {"U", "D", "L", "R", "F", "B"};
    Serial.print(faceNames[faceIdx]);
    if (q == 2) Serial.print("2");
    else if (!cw) Serial.print("'");
    Serial.print(" ");

    executeMovePair(faceIdx, q, cw, -1, 0, true);
  }

  Serial.println("\nScramble done.");
}

// Interactive State Machine for Serial UX
void loop() {
  switch (menuState) {

    case SHOW_MAIN_MENU: {
      Serial.println("\n=================================");
      Serial.println("       RUBIK'S CUBE CONTROL      ");
      Serial.println("=================================");
      Serial.println("1 -> Enter Custom Cube String (or MIX command)");
      Serial.println("2 -> Run a Pre-built Pattern");
      Serial.print("Select an option (1-2): ");
      menuState = WAIT_MAIN_CHOICE;
      break;
    }

    case WAIT_MAIN_CHOICE: {
      if (Serial.available() > 0) {
        String choice = Serial.readStringUntil('\n');
        choice.trim();

        if (choice == "1") {
          Serial.println("\n[Custom String Mode Selected]");
          Serial.println("Enter algorithm sequence (e.g., R U R' U') or 'MIX n' to scramble:");
          menuState = WAIT_STRING_INPUT;
        }
        else if (choice == "2") {
          Serial.println("\n=================================");
          Serial.println("        SELECT A PATTERN         ");
          Serial.println("=================================");
          for (int i = 0; i < 16; i++) {
            Serial.print(i + 1);
            Serial.print(". ");
            Serial.print(patterns[i].name);
            Serial.print(" (");
            Serial.print(patterns[i].sequence);
            Serial.println(")");
          }
          Serial.print("Select a pattern number (1-16): ");
          menuState = WAIT_PATTERN_CHOICE;
        }
        else {
          Serial.println("Invalid selection. Please type 1 or 2.");
          menuState = SHOW_MAIN_MENU;
        }
      }
      break;
    }

    case WAIT_STRING_INPUT: {
      if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        input.trim();

        if (input.length() > 0) {
          if (input.length() >= 3 && input.substring(0, 3).equalsIgnoreCase("MIX")) {
            int n = 20;
            if (input.length() > 3) {
              String arg = input.substring(3);
              arg.trim();
              if (arg.length() > 0) n = arg.toInt();
              if (n <= 0) n = 20;
            }
            scrambleCube(n);
          } else {
            Serial.print("Executing: ");
            Serial.println(input);
            executeSequence(input);
          }
        }
        menuState = SHOW_MAIN_MENU; // Loop back to main menu after execution
      }
      break;
    }

    case WAIT_PATTERN_CHOICE: {
      if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        input.trim();
        int patternIdx = input.toInt() - 1;

        if (patternIdx >= 0 && patternIdx < 16) {
          Serial.print("\nRunning Pattern: ");
          Serial.println(patterns[patternIdx].name);
          Serial.print("Sequence: ");
          Serial.println(patterns[patternIdx].sequence);

          executeSequence(patterns[patternIdx].sequence);

          Serial.println("Pattern Complete!");
        } else {
          Serial.println("Invalid selection. Returning to Main Menu.");
        }
        menuState = SHOW_MAIN_MENU; // Loop back to main menu after execution
      }
      break;
    }
  }
}