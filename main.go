package main

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"
)

type Accident struct {
	ID             int       `json:"id"`
	Region         string    `json:"region"`
	Date           time.Time `json:"date"`
	Fatalities     int       `json:"fatalities"`
	Injured        int       `json:"injured"`
	AccidentsCount int       `json:"accidents_count"`
}

const batchSize = 50
const outputFile = "accidents_data.json"

func main() {

	ch := make(chan Accident, 100)
	var wg sync.WaitGroup

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	wg.Add(1)
	go func() {
		defer wg.Done()
		regions := []string{"Москва", "Санкт-Петербург", "Казань", "Екатеринбург", "Новосибирск"}
		idCounter := 1

		for {
			select {
			case <-ctx.Done():
				fmt.Println("Получен сигнал завершения. Остановка сборщика...")
				close(ch)
				return
			default:
				accident := Accident{
					ID:             idCounter,
					Region:         regions[rand.Intn(len(regions))],
					Date:           time.Now().Add(-time.Duration(rand.Intn(1000)) * time.Hour),
					Fatalities:     rand.Intn(5),
					Injured:        rand.Intn(15),
					AccidentsCount: rand.Intn(10) + 1,
				}
				ch <- accident
				idCounter++
				time.Sleep(50 * time.Millisecond)
			}
		}
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		file, err := os.OpenFile(outputFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			fmt.Println("Ошибка открытия файла:", err)
			return
		}
		defer file.Close()

		var batch []Accident
		ticker := time.NewTicker(2 * time.Second)
		defer ticker.Stop()

		flush := func() {
			if len(batch) == 0 {
				return
			}
			for _, item := range batch {
				data, _ := json.Marshal(item)
				file.WriteString(string(data) + "\n")
			}
			fmt.Printf("Записан батч из %d записей\n", len(batch))
			batch = batch[:0]
		}

		for {
			select {
			case acc, ok := <-ch:
				if !ok {
					flush()
					fmt.Println("Канал закрыт, запись завершена.")
					return
				}
				batch = append(batch, acc)
				if len(batch) >= batchSize {
					flush()
				}
			case <-ticker.C:
				flush()
			}
		}
	}()

	<-ctx.Done()
	wg.Wait()
	fmt.Println("Программа успешно завершена.")
}
