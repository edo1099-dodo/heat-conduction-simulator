"""
Body.py
Represents a physical body capable of absorbing or releasing thermal energy.
"""


class Body:
    def __init__(self, mass: float, heat_capacity: float, temperature: float):
        """
        Initialize a physical body.

        :param mass: Mass of the body in kg (must be > 0)
        :param heat_capacity: Specific heat capacity in J/(kg*°C) (must be > 0)
        :param temperature: Initial temperature in °C (must be >= 0)
        """
        if mass <= 0:
            raise ValueError("Mass must be greater than 0 kg.")
        if heat_capacity <= 0:
            raise ValueError("Heat capacity must be greater than 0 J/(kg*°C).")
        if temperature < 0:
            raise ValueError("Temperature must be 0 °C or higher.")

        self.mass = float(mass)
        self.heat_capacity = float(heat_capacity)
        self.temperature = float(temperature)

    def add_heat(self, heat_joules: float) -> float:
        """
        Add (or remove, if negative) thermal energy in Joules and update temperature.

        Equations:
            delta_T = delta_Q / (m * c)
            New_T   = T + delta_T

        :param heat_joules: Amount of heat added in Joules (can be negative)
        :return: Updated temperature in °C
        """
        delta_t = heat_joules / (self.mass * self.heat_capacity)
        self.temperature += delta_t
        return self.temperature


if __name__ == "__main__":
    # Direct execution self-test as specified in Stage 1
    test_body = Body(mass=100, heat_capacity=0.15, temperature=200)

    temp_after_plus_20 = test_body.add_heat(20)
    print(f"Temperature after adding 20 J: {temp_after_plus_20:.4f} °C")

    temp_after_minus_40 = test_body.add_heat(-40)
    print(f"Temperature after adding -40 J: {temp_after_minus_40:.4f} °C")
