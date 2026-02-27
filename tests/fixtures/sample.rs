pub struct Animal {
    pub name: String,
    pub age: u32,
}

impl Animal {
    pub fn new(name: String) -> Self {
        Animal { name, age: 0 }
    }

    pub fn speak(&self) -> String {
        String::from("...")
    }
}

pub struct Dog {
    pub breed: String,
}

impl Dog {
    pub fn speak(&self) -> String {
        String::from("Woof!")
    }
}

pub struct Cat {
    indoor: bool,
}

impl Cat {
    pub fn new(indoor: bool) -> Self {
        Cat { indoor }
    }
}

pub trait MakeSound {
    fn make_sound(&self) -> String;
}

impl MakeSound for Dog {
    fn make_sound(&self) -> String {
        self.speak()
    }
}
