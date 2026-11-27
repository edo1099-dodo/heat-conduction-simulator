class Body:
    def __init__(self, mass, heat_capacity, temperature):
        if mass <= 0:
            raise ValueError("Mass must be greater than 0 kg.")
        if heat_capacity <= 0:
            raise ValueError("Heat capacity must be greater than 0 J/(kg*°C).")
        if temperature < 0:
            raise ValueError("Temperature must be 0 °C or higher.")

        self.mass = float(mass)
        self.heat_capacity = float(heat_capacity)
        self.temperature = float(temperature)

    def add_heat(self, heat_joules):
        # delta_T = delta_Q / (m * c)
        delta_t = heat_joules / (self.mass * self.heat_capacity)
        self.temperature = self.temperature + delta_t
        return self.temperature


if __name__ == "__main__":
    body = Body(100, 0.15, 200)

    t1 = body.add_heat(20)
    print(f"After +20 J: {t1:.4f} °C")

    t2 = body.add_heat(-40)
    print(f"After -40 J: {t2:.4f} °C")
