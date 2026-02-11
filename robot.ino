enum Face { U, D, L, R, F, B };

const int motors[6][3] = {
  {13, 14, 33}, // 0: U
  {26, 25, 27}, // 1: D
  {32, 15, 19}, // 2: L
  {23, 22, 18}, // 3: R
  {4, 2, 5},    // 4: F
  {12, 21, 17}  // 5: B
};

int steps90[6] = {1610, 1610, 810, 810, 800, 810};

// Speed Profiles
const int SIDE_START_DELAY = 800;
const int SIDE_TARGET_DELAY = 100;
const int SIDE_RAMP = 200;

const int UD_START_DELAY = 800;
const int UD_TARGET_DELAY = 200;
const int UD_RAMP = 250;

const int BRAKE_TIME = 100;

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 6; i++) {
    pinMode(motors[i][0], OUTPUT);
    pinMode(motors[i][1], OUTPUT);
    pinMode(motors[i][2], OUTPUT);
    digitalWrite(motors[i][2], HIGH);
  }
  Serial.println("--- Full Scramble Parser Ready ---");
  Serial.println("Paste algorithm (e.g., R2B'LD) and hit Enter.");
}

void moveFace(int motorIdx, int quarters, bool clockwise) {
  long totalSteps = (long)steps90[motorIdx] * quarters;
  int startDelay, targetDelay, rampSteps;

  if (motorIdx == U || motorIdx == D) {
    startDelay = UD_START_DELAY; targetDelay = UD_TARGET_DELAY; rampSteps = UD_RAMP;
  } else {
    startDelay = SIDE_START_DELAY; targetDelay = SIDE_TARGET_DELAY; rampSteps = SIDE_RAMP;
  }

  int limitSpeed = (motorIdx == U || motorIdx == D || motorIdx == B) ? targetDelay / 2 : targetDelay;

  digitalWrite(motors[motorIdx][2], LOW); // Enable
  delay(10);
  digitalWrite(motors[motorIdx][1], clockwise ? HIGH : LOW);

  for (long i = 0; i < totalSteps; i++) {
    int currentDelay = (i < rampSteps) ? startDelay - ((startDelay - limitSpeed) * i / rampSteps) : limitSpeed;
    digitalWrite(motors[motorIdx][0], HIGH);
    delayMicroseconds(currentDelay);
    digitalWrite(motors[motorIdx][0], LOW);
    delayMicroseconds(currentDelay);
  }

  delay(BRAKE_TIME);
  digitalWrite(motors[motorIdx][2], HIGH); // Disable
}

void processCommand(String input) {
  input.toUpperCase();
  int i = 0;

  while (i < input.length()) {
    char move = input[i];
    int faceIdx = -1;

    // Map char to Face index
    if (move == 'U') faceIdx = U;
    else if (move == 'D') faceIdx = D;
    else if (move == 'L') faceIdx = L;
    else if (move == 'R') faceIdx = R;
    else if (move == 'F') faceIdx = F;
    else if (move == 'B') faceIdx = B;

    if (faceIdx != -1) {
      int quarters = 1;
      bool clockwise = true;

      // Look at the character AFTER the letter
      if (i + 1 < input.length()) {
        char modifier = input[i + 1];
        if (modifier == '\'' || modifier == 'I') {
          clockwise = false;
          i++; // Skip the modifier in next loop
        } else if (modifier == '2') {
          quarters = 2;
          i++; // Skip the modifier in next loop
        }
      }

      Serial.print("Executing: "); Serial.print(move);
      if (quarters == 2) Serial.print("2"); else if (!clockwise) Serial.print("'");
      Serial.println();

      moveFace(faceIdx, quarters, clockwise);
      delay(200); // Settle time between different moves in a string
    }
    i++;
  }
  Serial.println("--- Scramble Complete ---");
}

void loop() {
  if (Serial.available() > 0) {
    String incoming = Serial.readStringUntil('\n');
    incoming.trim(); // Remove spaces or hidden characters
    if (incoming.length() > 0) {
      processCommand(incoming);
    }
  }
}